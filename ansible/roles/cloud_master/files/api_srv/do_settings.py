import json
import os

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
with open(os.path.join(SCRIPT_DIR, "do_vulnimages.json")) as vulnimages_file:
    vulnimages = json.load(vulnimages_file)

CLOUD_FOR_NEW_VMS = "hitb"
CLOUD_FOR_DNS = "hitb"
DOMAIN = "ctf.hitb.org"

CLOUDS = {
    "hitb": {
        "region": "ams3",
        "router_image": 89427587,
        "router_size": "s-1vcpu-2gb",
        "vulnimages": vulnimages,
        "vulnimage_size": "s-2vcpu-4gb",
        "ssh_keys": [27173548, 32353017]
    },
    "bay": {
        "router_image": 0,
        "vulnimages": {3: 0},
        "ssh_keys": [0, 0]
    }
}

DO_SSH_ID_FILE = "hitb2021_do_deploy"

