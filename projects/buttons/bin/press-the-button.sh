# Script invoked from user pressing the button

#!/bin/bash

option="$1"
PREEMPTIBLE="--preemptible"
case $option in
    -p|--prod|--production)
    unset PREEMPTIBLE
esac

if [ -n "$PREEMPTIBLE" ]; then
   echo "If you need a permanent version of this server, run the following:"
   echo ".bin/press-the-button.sh --production"
else
   echo "Starting a production version of button FOO..."
fi

NEW_UUID=$(cat /dev/urandom | tr -dc 'a-z0-9' | fold -w 4 | head -n 1)
ZONE=us-west1-c

gcloud compute instances create fusion-sockitter-$NEW_UUID \
--machine-type "n1-standard-4" \
--image "ubuntu-1604-xenial-v20180612" \
--image-project "ubuntu-os-cloud" \
--boot-disk-size "200" \
--boot-disk-type "pd-ssd" \
--boot-disk-device-name "$NEW_UUID" \
--zone $ZONE \
--labels type=fusion \
--tags fusion \
$PROD \
--metadata-from-file startup-script=bin/start-button.sh

sleep 15

IP=$(gcloud compute instances describe fusion-sockitter-$NEW_UUID --zone $ZONE  | grep natIP | cut -d: -f2 | sed 's/^[ \t]*//;s/[ \t]*$//')
gcloud compute firewall-rules create fusion --allow tcp:8764
gcloud compute firewall-rules create fusion --allow tcp:8763
gcloud compute firewall-rules create fusion-appkit --allow tcp:8080
gcloud compute firewall-rules create fusion-webapp --allow tcp:8780

echo "Button FOO pressed and launched:"
echo "Fusion UI available in a few minutes at: http://$IP:8764"