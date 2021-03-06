# Lucidworks Streams
This is the [Lucidworks](https://lucidworks.com/) Streams repository. This repository is maintained by the Streams Team at Lucidworks. Streams are Fusion application templates designed to educate, inspire and create meaningful search/AI product marketing discourse in and around emerging technology markets.

You can view Streams episodes over on [Lucidwork's YouTube Channel](https://www.youtube.com/user/LucidWorksSearch).

## Stream Projects
The following streamable projects may be launched for demonstration purposes on Google Cloud Compute and/or modified to run on other cloud platforms. These projects typically include a video guide and accompanying Fusion application.

- [Buttons](https://github.com/lucidworks/streams/tree/master/projects/buttons) - The Buttons project implements [https://streams.lucidworks.com/](https://streams.lucidworks.com/), which provides Github users a means to demo various Fusion based applications. A comprehensive list of templates for the projects will soon be available at [Lucidworks Labs](https://lucidworks.com/labs).

- [Samjna Image Perception for Fusion](https://github.com/lucidworks/streams/tree/master/projects/samjna) - Samjna (sam-ji-na) adds image-based perception capabilities to Lucidwork's [Fusion 4.x](https://lucidworks.com/products/fusion-server/) using a general AI network.

- [Sockitter Twitter Tool for Fusion](https://github.com/lucidworks/streams/tree/master/projects/sockitter) - Sockitter adds powerful semantic graph capabilities to Lucidwork's [Fusion 4.x](https://lucidworks.com/products/fusion-server/), allowing it to do real-time traversal and ranking of data relationships on Twitter. (Please note that Twitter has suspended support for their streaming APIs, so this project no longer works.

### Stream Seeds
The following gists cover various use cases for Fusion using a base cloud template. Seeds do NOT provide video guides or application zips and require manual configuration of Fusion to achieve results.

- [Indexing XKCD with Lucidwork's Fusion and Google Image API](https://gist.github.com/kordless/f63a6ec9a5bfde81b811d439282ef2d2)

If you find these demos useful to you or your company's search processes, please star this repo and get in touch with [Lucidworks directly](https://lucidworks.com/ppc/lucidworks-fusion-solr/?utm_source=streams) for more information. 

## Launching a Fusion 4.x Demo Instance in 5 Minutes On Lucidworks Labs
A demo instance of Fusion 4.x may be started by using your Github account to login to [Lucidworks Labs](https://lucidworks.com/labs). Click the button below and follow the instructions provided on the Streams Labs page to begin using Fusion.

[![Launch Starter](https://img.shields.io/badge/launch-starter-green.svg)](https://streams.lucidworks.com/instance/create/starter)

**Note: An email address is required to start an instance on Labs.**

## Launching a Fusion 4.x Instance on Your Own Cloud
A demo instance of Fusion 4.x may be started on your own Google Cloud account by running a simple script which may be checked out from Github using the `git` command from the Google Cloud Shell. To start a new shell, navigate to [https://console.cloud.google.com/](https://console.cloud.google.com/) and click on the `>_` button toward the top right of the screen.

![animation](https://github.com/lucidworks/streams/blob/master/assets/images/cloudshell.gif?raw=true)

Once you are in the Google Cloud Console, you can download the startup script from Github by entering the following:

**Commands:**
```
git clone https://github.com/lucidworks/streams
cd streams/scripts
```

**Sample Output:**
```
$ git clone https://github.com/lucidworks/streams
Cloning into 'streams'...
remote: Counting objects: 2420, done.
remote: Compressing objects: 100% (24/24), done.
remote: Total 2420 (delta 12), reused 21 (delta 8), pack-reused 2388
Receiving objects: 100% (2420/2420), 94.40 MiB | 47.15 MiB/s, done.
Resolving deltas: 100% (1247/1247), done.

$ cd streams
$ ls
episodes  images  projects  README.md  scripts
$ cd scripts
$ ls
start-fusion-4.sh  start-fusion-gcp.sh  start-proxy.sh  start-tensorflow.sh  start-twigkit.sh  start-ubuntu.sh
```

To start the Fusion demo instance, simply run the `start-fusion-4.sh` script:

**Command:**
```
./start-fusion-4.sh
```

**Sample Output:**
```
$ ./start-fusion-4.sh
Created [https://www.googleapis.com/compute/v1/projects/wisdom-172109/zones/us-central1-a/instances/fusion-4-orur].
NAME                ZONE           MACHINE_TYPE   PREEMPTIBLE  INTERNAL_IP  EXTERNAL_IP     STATUS
fusion-4-orur  us-central1-a  n1-standard-8  true         10.128.0.5   104.197.75.229  RUNNING
Thank you for running me. Here's what I know:
Fusion UI available in a few minutes at: http://104.197.75.229:8764
API access available in a few minutes at: https://104.197.75.229:8764/api/...
API Docs are here: https://doc.lucidworks.com/fusion-server/4.0/index.html
```

The startup process takes about 10 minutes to complete. After that, you can click on the `Fusion UI URL` and navigate to the Fusion UI!

![animation](https://github.com/lucidworks/streams/blob/master/assets/images/startfusion.gif?raw=true)

## Google Cloud Setup
If you do not already have a Google Cloud account, head on over to [https://cloud.google.com/](https://cloud.google.com/) and click on the `TRY IT FREE` button to get a $300 credit with a new account. You will need to add a credit card to your account.

Once you have your account configured, you will be able to start a preemptible instance running Fusion 4.x, *which will live at most for 24 hours*. The run cost for this instance is about $1 per 24 hours, but your mileage may vary. Do keep in mind you may need to restart your instance from time to time.

If you have any questions or comments for the Stream Team, [please open an issue](https://github.com/lucidworks/streams/issues)!
