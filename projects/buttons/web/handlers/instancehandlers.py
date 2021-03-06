# standard library imports
import logging, os
import urllib, urllib2, httplib2
import hashlib, json
import time, datetime

from lib.dateutil import parser as DUp

import webapp2

import config
import web.forms as forms
from web.basehandler import BaseHandler
from web.basehandler import user_required, admin_required
from web.models.models import User, Instance, Stream
from lib import slack
from lib import utils

from lib.marketorestpython.client import MarketoClient

# API methods for keeping cloud status and appengine db in sync via fastner box API
class InstanceTenderHandler(BaseHandler):
    def get(self):
        try:
            # grab a list of instances from the Fastener API
            http = httplib2.Http(timeout=15)
            url = '%s/api/instance/list?token=%s' % (config.fastener_host_url, config.fastener_api_token)
            response, content = http.request(url, 'GET')
        
            # list of instances from Google Cloud (see ./fastener/sample-output.json)
            gcinstances = json.loads(content)

            if len(gcinstances) > 0:
                message = "ok"
            else:
                message = "no instances were returned from fastener API"

        except Exception as ex:
            gcinstances = []
            message = "failed to contact fastener API"

        # list of instances from db
        instances = Instance.get_all()

        # bail if we didn't get any instances from Google
        if len(gcinstances) == 0:
            params = { 
                "message": message, 
                "gc_count": len(gcinstances), 
                "db_count": len(instances)
            }
            self.response.headers['Content-Type'] = "application/json"
            return self.render_template('api/tender.json', **params)
            ######

        # loop through list of instances in local or production DB
        for instance in instances:
            name = instance.name

            # loop through the instances we got from google
            for gcinstance in gcinstances:

                # check if the names match
                if name == gcinstance['name']:
                    # got a match
                    try:
                        # grab the IP address and status
                        instance.ip = gcinstance['networkInterfaces'][0]['accessConfigs'][0]['natIP']
                        instance.status = gcinstance['status']

                        # check if the box is running fusion admin yet
                        try:
                            # fast fail connection for checking if fusion is up
                            http_test = httplib2.Http(timeout=2)
                            test_url = 'http://%s:8764' % instance.ip
                            response, content = http_test.request(test_url, 'GET')
                            test_status = response['status']
                        except:
                            test_status = "404"

                        # set admin_link if box is running and test comes back 200
                        if gcinstance['status'] == "RUNNING" and test_status == "200":
                            instance.admin_link = test_url

                            # build app link and update, if it exists
                            if instance.stream.get().app_stub:
                                app_stub = instance.stream.get().app_stub
                                instance.app_link = "http://%s%s" % (instance.ip, app_stub)
                            else:
                                instance.app_link = None  
                        else:
                            # show the box is in configuration mode
                            instance.status = "CONFIGURING"
                            instance.admin_link = None
                            instance.app_link = None

                    except:
                        # got limited or no data about instance
                        instance.ip = "None"
                        instance.status = gcinstance['status']
                        instance.admin_link = None
                        instance.app_link = None

                    # instance has been terminated
                    if gcinstance['status'] == "TERMINATED":
                        # set start time to far in the past
                        instance.started = instance.created - datetime.timedelta(0, 604800)
                        pass

                    instance.put()

                    break # no need to keep looking

                else:
                    # instance doesn't match
                    pass

            else:
                # no instances were found on Google Cloud for this local instance record
                if instance.created < datetime.datetime.now() - datetime.timedelta(0, 300):
                    slack.slack_message("DELETING instance %s's record from database. No instance found on Google Cloud." % name)
                    instance.key.delete()
                else:
                    # only delete if instance create time is greater than 30 minutes...
                    slack.slack_message("WAITING to delete instance %s's record from database. No instance found on Google Cloud." % name)

        else:
            # no instances in db
            pass

        # cleanup stray and EOL instances
        for gcinstance in gcinstances:
            instance = Instance.get_by_name(gcinstance['name'])

            if instance:
                name = instance.name

                # if instance is expired, end it
                if instance.expires < datetime.datetime.now():
                    # make the instance call to the control box
                    try:
                        http = httplib2.Http(timeout=10)
                        url = '%s/api/instance/%s/delete?token=%s' % (
                            config.fastener_host_url, 
                            name,
                            config.fastener_api_token
                        )

                        # pull the response back
                        response, content = http.request(url, 'GET', None, headers={})
                        if content['status'] == "PENDING":
                            instance.key.delete()          
                            slack.slack_message("DELETING instance %s's from Google Cloud." % name)
                    
                    except:
                        slack.slack_message("ERROR: failed deleting instance %s's from Google Cloud." % name)

            else:
                # instance wasn't found in db
                # make sure we don't delete non-demo instances
                name = gcinstance['name']

                if 'button' in name:
                    # handle dev vs. prod instances (need to stage cloud, but all mixed for now)
                    delete = False
                    if config.isdev:
                        if 'dev' in gcinstance['labels']['user']:
                            delete = True
                    else:
                        if 'prod' in gcinstance['labels']['user']:
                            delete = True

                    if delete:        
                        # make the instance call to the control box
                        try:
                            http = httplib2.Http(timeout=10)
                            url = '%s/api/instance/%s/delete?token=%s' % (
                                config.fastener_host_url, 
                                name,
                                config.fastener_api_token
                            )

                            # pull the response back
                            response, content = http.request(url, 'GET', None, headers={})

                            if content['status'] == "PENDING":      
                                slack.slack_message("DELETING instance %s's from Google Cloud." % name)
                            else:
                                slack.slack_message("ERROR: funky content returned while deleting instance %s's from Google Cloud." % name)
                        
                        except:
                            slack.slack_message("ERROR: failed deleting instance %s's from Google Cloud." % name)

        else:
            # no instances from cloud - this should never run
            pass

        params = { 
            "message": message, 
            "gc_count": len(gcinstances), 
            "db_count": len(instances)
        }

        self.response.headers['Content-Type'] = "application/json"
        return self.render_template('api/tender.json', **params)
        ######


# handle an instance start by showing a non-authenticated dashboard page w/ a dialog
# if a user exists, forwards to next handler to start the instance
# /instance/create/<sid>
class StreamsStarterPage(BaseHandler):
    def get(self, sid=None):
        try:
            user_info = User.get_by_id(long(self.user_id))
            if user_info:
                self.redirect_to('streams-start3', sid=sid)
            else:
                raise Exception('No user.')
        except:
            pass

        params = {'dialog': True}
        return self.render_template('user/dashboard.html', **params)


# provide useful link to directly start an instance from another page
# /instance/create/<sid>/launch
# this method and the InstancesListHandler POST method use duplicated code (take care, needs to be refactored)
class StreamsStarterHandler(BaseHandler):
    @user_required
    def get(self, sid):
        # know the user
        user_info = User.get_by_id(long(self.user_id))

        # check if we have their email
        if not user_info.email:
            self.add_message('Please update your email address before starting an instance!', 'warning')
            return self.redirect_to('account-settings')

        # look up user's instances
        db_instances = Instance.get_all()

        # check the user's limits
        instance_count = 0
        for db_instance in db_instances:
            # limit to instances the user has started
            if db_instance.user == user_info.key:
                instance_count = instance_count + 1

        # warn and redirect if limit is reached
        if (instance_count + 1) > user_info.max_instances:
            self.add_message('Instance limit reached. This account may only start %s instances. Please delete an existing instance to start a new one!' % user_info.max_instances, 'warning')
            return self.redirect_to('instances-list')

        # get stream
        stream = Stream.get_by_sid(sid)

        # make the instance call to the control box
        http = httplib2.Http(timeout=10)

        # where and who created it
        if config.isdev:
            iuser = "%s-%s" % ("dev", user_info.username)
        else:
            iuser = "%s-%s" % ("prod", user_info.username)

        url = '%s/api/stream/%s?token=%s&user=%s' % (
            config.fastener_host_url,
            sid,
            config.fastener_api_token,
            iuser
        )

        try:
            # pull the response back TODO add error handling
            response, content = http.request(url, 'POST', None, headers={})
            gcinstance = json.loads(content)
            name = gcinstance['instance']
            password = gcinstance['password']

            if name == "failed":
                raise Exception("Instance start failed.")

            # set up an instance (note there are two ways to create an instance - see below)
            instance = Instance(
                name = name,
                status = "PROVISIONING",
                user = user_info.key,
                stream = stream.key,
                password = password,
                expires = datetime.datetime.now() + datetime.timedelta(0, 604800),
                started = datetime.dateime.now()
            )
            instance.put()

            slack.slack_message("Instance type %s created for %s!" % (stream.name, user_info.username))

            # give the db a second to update
            if config.isdev:
                time.sleep(1)

            self.add_message('Instance created! Give the system a few minutes to start %s.' % stream.name, 'success')

            params = {'name': name}
            return self.redirect_to('instance-detail', **params)


        except:
            self.add_message('The system is currently busy with other instances. Please try again in a few minutes.', 'warning')
            return self.redirect_to('instances-list')


# list of a user's instances and create new instance
# this method and the StreamsStarterHandler GET method use duplicated code (take care, needs to be refactored)
class InstancesListHandler(BaseHandler):
    @user_required
    def get(self, sid=None):
        # lookup user's auth info
        user_info = User.get_by_id(long(self.user_id))

        # redirect to a POST if we have a sid in the URL
        if sid and user_info.email:
            return self.post(sid)
        try:
            if not user_info.email or not user_info.name or not user_info.company:
                need_more_info = True
            else:
                need_more_info = False
        except:
            need_more_info = True

        # look up user's instances
        db_instances = Instance.get_all()

        # work around index warning/errors using a .filter() in models.py
        instances = []
        for db_instance in db_instances:
            # limit to instances the user has started
            if db_instance.user == user_info.key:
                instances.append(db_instance)

        streams = Stream.get_all()

        params = {
            'instances': instances,
            'num_instances': len(instances),
            'streams': streams,
            'user_id': self.user_id,
            'user_info': user_info,
            'sid': sid,
            'need_more_info': need_more_info
        }

        return self.render_template('instance/list.html', **params)

    @user_required
    def post(self, sid=None):
        # know the user
        user_info = User.get_by_id(long(self.user_id))

        if sid and user_info.email:
            
            # get form values
            stream = Stream.get_by_sid(sid)

            # look up user's instances
            db_instances = Instance.get_all()

            # check the user's limits
            instance_count = 0
            for db_instance in db_instances:
                # limit to instances the user has started
                if db_instance.user == user_info.key:
                    instance_count = instance_count + 1

            # warn and redirect if limit is reached
            if (instance_count + 1) > user_info.max_instances:
                self.add_message('Instance limit reached. This account may only start %s instances. Please delete an existing instance to start a new one!' % user_info.max_instances, 'warning')
                return self.redirect_to('instances-list')

            # make the instance call handle
            http = httplib2.Http(timeout=10)
            
            # where and who created it
            if config.isdev:
                iuser = "%s-%s" % ("dev", user_info.username)
            else:
                iuser = "%s-%s" % ("prod", user_info.username)

            # build url to create new instance from stream
            url = '%s/api/stream/%s?token=%s&user=%s' % (
                config.fastener_host_url, 
                sid, 
                config.fastener_api_token,
                iuser
            )

            try:
                # pull the response back TODO add error handling
                response, content = http.request(url, 'POST', None, headers={})
                print content
                gcinstance = json.loads(content)
                name = gcinstance['instance']
                password = gcinstance['password']


                if name == "failed":
                    raise Exception("Instance start failed.")

                # set up an instance 
                instance = Instance(
                    name = name,
                    status = "PROVISIONING",
                    user = user_info.key,
                    stream = stream.key,
                    password = password,
                    expires = datetime.datetime.now() + datetime.timedelta(0, 604800),
                    started = datetime.datetime.now()
                )
                instance.put()

                slack.slack_message("Instance type %s created for %s!" % (stream.name, user_info.username))

                # give the db a second to update
                if config.isdev:
                    time.sleep(1)

                self.add_message('Instance created! Grab some coffee and wait for %s to start.' % stream.name, 'success')

                params = {'name': name}
                return self.redirect_to('instance-detail', **params)

            except:
                self.add_message('The system is currently busy with other instances. Please try again in a few minutes.', 'warning')
                return self.redirect_to('instances-list')

        else:
            # email update sumbission
            if not self.form.validate():
                self.add_message("There were errors validating your email address.", "error")
                return self.get()

            email = self.form.email.data.strip()

            user_info = User.get_by_id(long(self.user_id))
            user_info.email = email.strip()
            user_info.put()

            if len(email) > 3 and not config.isdev:
                name = user_info.name
                try:
                    mc = MarketoClient(config.munchkin_id, config.mclient_id, config.mclient_secret)
                    try:
                        first = name.split()[0]
                    except:
                        first = ""

                    try:
                        last = name.split()[1]
                    except:
                        last = ""

                    try:
                        company = user_info.company
                    except:
                        company = "None"

                    leads = [{
                        "email": user_info.email,
                        "firstName": first,
                        "lastName": last,
                        "company": company
                    }]
                    lead = mc.execute(
                        method='push_lead',
                        leads=leads,
                        lookupField='email',
                        programName='Lucidworks Streams - GitHub',
                        programStatus='Visited'
                    )

                except Exception as ex:
                    slack.slack_message("Marketo lead create failed because %s." % ex)

            slack.slack_message("We got %s to update their email for instance launch!" % user_info.username)

            self.add_message("Thank you! Your email has been updated.", 'success')
            
            # redirect back to GET on list, but with a sid AND email in place this time to create
            if sid:
                return self.redirect_to('streams-start', sid=sid)
            else:
                return self.redirect_to('instances-list')

    @webapp2.cached_property
    def form(self):
        return forms.EmailForm(self)


class InstanceControlHandler(BaseHandler):
    @user_required
    def get(self, name, command):
        # lookup user's auth info
        user_info = User.get_by_id(long(self.user_id))

        # delete instance
        instance = Instance.get_by_name(name)

        if not instance:
            params = {}
            return self.redirect_to('instances-list', **params)
        else:
            # check user owns it
            if long(instance.user.id()) != long(self.user_id):
                params = {"response": "failure", "message": "instance %s not owned by calling user" % name}
                response.set_status(500)
            else:
                # start the instance
                if command == "start" and instance.status != "RUNNING":
                    # make the instance call to the control box
                    http = httplib2.Http(timeout=10)
                    url = '%s/api/instance/%s/start?token=%s' % (
                        config.fastener_host_url, 
                        name,
                        config.fastener_api_token
                    )

                    # pull the response back TODO add error handling
                    response, content = http.request(url, 'GET', None, headers={})

                    # update if google returns pending
                    if json.loads(content)['status'] == "PENDING":
                        params = {"response": "success", "message": "instance %s started" % name }
                        instance.status = "STAGING"
                        instance.started = datetime.datetime.now()
                        instance.put()
                    else:
                        params = {"response": "failure", "message": "instance %s operation failure" % name }
                        response.set_status(500)

                # delete the instance - C'est la vie
                elif command == "delete":
                    # make the instance call to the control box
                    http = httplib2.Http(timeout=10)
                    url = '%s/api/instance/%s/delete?token=%s' % (
                        config.fastener_host_url, 
                        name,
                        config.fastener_api_token
                    )

                    try:
                        # pull the response back TODO add error handling
                        response, content = http.request(url, 'GET', None, headers={})

                        # delete if google returns pending
                        if json.loads(content)['status'] == "PENDING":
                            params = {"response": "success", "message": "instance %s deleted" % name }
                            instance.key.delete()
                        else:
                            params = {"response": "failure", "message": "instance %s operation failure" % name }
                            response.set_status(500)
                    except:
                        params = {"response": "failure", "message": "instance %s failure" % name }
                        # probably shouldn't do this, but whatever
                        instance.key.delete()

                # just the status
                elif command == "status":
                    params = {"instance": instance}
                    self.response.headers['Content-Type'] = "application/json"
                    return self.render_template('api/instance.json', **params)

                else:
                    params = {"response": "failure", "message": "bad command, skippy" }                    
                    response.set_status(500)
                
                self.response.headers['Content-Type'] = "application/json"
                return self.render_template('api/response.json', **params)


# instance detail page
class InstanceDetailHandler(BaseHandler):
    @user_required
    def get(self, name):
        # lookup user's auth info
        user_info = User.get_by_id(long(self.user_id))

        # look up user's instances
        instance = Instance.get_by_name(name)

        if not instance:
            params = {}
            return self.redirect_to('instances-list', **params)

        stream = Stream.get_by_id(instance.stream.id())

        if utils.read_cookie(self, "guide") == "closed":
            guide = False
        else:
            guide = True

        params = {
            'guide': guide,
            'instance': instance,
            'stream': stream
        }

        return self.render_template('instance/detail.html', **params)


# instance detail page
class InstanceConsoleHandler(BaseHandler):
    @user_required
    def get(self, name):
        # lookup user's auth info
        user_info = User.get_by_id(long(self.user_id))

        # look up user's instances
        instance = Instance.get_by_name(name)

        self.response.headers['Content-Type'] = "text/plain"

        if not instance:
            params = {"contents": "Waiting on serial console output..."}
            return self.render_template('instance/console.txt', **params)

        try:
            # update list of instances we have
            http = httplib2.Http()
            url = '%s/api/instance/%s/console?token=%s' % (config.fastener_host_url, name, config.fastener_api_token)
            response, content = http.request(url, 'GET')
            stuff = json.loads(content)

            params = {"contents": stuff['contents']}
        except Exception as ex:
            params = {"contents": "Waiting on serial console output..."}

        return self.render_template('instance/console.txt', **params)