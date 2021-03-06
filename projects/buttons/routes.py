from webapp2_extras.routes import RedirectRoute
from web.handlers import sitehandlers, adminhandlers, userhandlers, instancehandlers, emailhandlers
# from web.handlers import foo

secure_scheme = 'https'

_routes = [
	# website
	RedirectRoute('/', sitehandlers.IndexHandler, name='index', strict_slash=True),
	RedirectRoute('/labs', sitehandlers.IndexHandler, name='index', strict_slash=True),
	RedirectRoute('/labdocs/', sitehandlers.DocsHandler, name='labdocs', strict_slash=True),
	
	# users
	RedirectRoute('/login/', userhandlers.LoginHandler, name='login', strict_slash=True),
	RedirectRoute('/logout/', userhandlers.LogoutHandler, name='logout', strict_slash=True),
	RedirectRoute('/login/complete', userhandlers.CallbackLoginHandler, name='login-complete', strict_slash=True),
	RedirectRoute('/login/complete/<npid>', userhandlers.CallbackLoginHandler, name='login-complete2', strict_slash=True),
	RedirectRoute('/login/tfa', userhandlers.TwoFactorLoginHandler, name='login-tfa', strict_slash=True),
	RedirectRoute('/settings/', userhandlers.SettingsHandler, name='account-settings', strict_slash=True),
	RedirectRoute('/settings/tfa', userhandlers.TwoFactorSettingsHandler, name='account-tfa', strict_slash=True),
	RedirectRoute('/dashboard/', userhandlers.DashboardHandler, name='account-dashboard', strict_slash=True),

	# user's instances
	RedirectRoute('/instances/', instancehandlers.InstancesListHandler, name='instances-list', strict_slash=True),

	# launch instances links	
	RedirectRoute('/instance/create/<sid>', instancehandlers.StreamsStarterPage, name='streams-start', strict_slash=True),	
	RedirectRoute('/instances/create/<sid>', instancehandlers.StreamsStarterPage, name='streams-start2', strict_slash=True),
	RedirectRoute('/instance/create/<sid>/launch', instancehandlers.InstancesListHandler, name='streams-start3', strict_slash=True),	

	# other instance things
	RedirectRoute('/instance/tender', instancehandlers.InstanceTenderHandler, name='instance-tender', strict_slash=True),
	RedirectRoute('/instance/<name>', instancehandlers.InstanceDetailHandler, name='instance-detail', strict_slash=True),
	RedirectRoute('/instance/<name>/console', instancehandlers.InstanceConsoleHandler, name='instance-console', strict_slash=True),
	RedirectRoute('/instance/<name>/<command>', instancehandlers.InstanceControlHandler, name='instance-control', strict_slash=True),

	# tasks
	RedirectRoute('/tasks/mail/', sitehandlers.SendEmailHandler, name='taskqueue-send-email', strict_slash=True),

	# admin
	RedirectRoute('/admin/streams/', adminhandlers.AdminStreamsHandler, name='admin-streams', strict_slash=True),
	RedirectRoute('/admin/instances/', adminhandlers.AdminInstancesHandler, name='admin-instances', strict_slash=True),
	RedirectRoute('/admin/users/', adminhandlers.AdminUsersHandler, name='admin-users', strict_slash=True),
	RedirectRoute('/admin/users/export/', adminhandlers.AdminUsersExportHandler, name='admin-users-export', strict_slash=True),
	RedirectRoute('/admin/users/<user_id>', adminhandlers.AdminUsersHandler, name='admin-users-edit', strict_slash=True),

	# admin deletes
	RedirectRoute('/admin/streams/<stream_id>/', adminhandlers.AdminStreamsHandler, name='admin-streams-sid', strict_slash=True),
	RedirectRoute('/admin/instances/<instance_id>/', adminhandlers.AdminInstancesHandler, name='admin-instances-name', strict_slash=True),
	
	# api/slack
	RedirectRoute('/api/stream/<sid>', adminhandlers.AdminStreamsAPIHandler, name='api-streams', strict_slash=True),
	RedirectRoute('/api/instance/<name>', adminhandlers.AdminInstancesAPIHandler, name='api-instances', strict_slash=True),
	RedirectRoute('/slack', sitehandlers.SlackbotHandler, name='slack-card', strict_slash=True)
]

def get_routes():
	return _routes

def add_routes(app):
	if app.debug:
		secure_scheme = 'http'
	for r in _routes:
		app.router.add(r)
