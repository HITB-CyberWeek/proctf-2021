#!/usr/bin/python3
# Developed by Alexander Bersenev from Hackerdom team, bay@hackerdom.ru

"""Lists vm snapshots"""


import sys
import time
import os
import traceback
import re
import subprocess

import do_api
from do_tokens import DO_TOKENS
from cloud_common import (log_progress, call_unitl_zero_exit, get_cloud_name,
                          get_image_name, get_snapshot_prefix, SSH_OPTS #, SSH_YA_OPTS
                          )

TEAM = int(sys.argv[1])
VMNUM = int(sys.argv[2])
# IMAGE_VM_NAME = "team%d" % TEAM
# SNAPSHOT_PREFIX = IMAGE_VM_NAME + "-"

def log_stderr(*params):
    print("Team %d:" % TEAM, *params, file=sys.stderr)


def main():
    image_state = open("db/team%d/serv%d_image_deploy_state" % (TEAM, VMNUM)).read().strip()

    if image_state == "NOT_STARTED":
        print("msg: ERR, vm is not started")
        return 1

    if image_state == "RUNNING":
        cloud_name = get_cloud_name(TEAM)
        if not cloud_name:
            log_stderr("no cloud_name, exiting")
            return 1

        token = DO_TOKENS[cloud_name]

        snapshots = do_api.list_snapshots(token)

        good_snapshots = []

        snapshot_prefix = get_snapshot_prefix(TEAM, VMNUM)

        for snapshot in snapshots:
            if not snapshot.get("name", "").startswith(snapshot_prefix):
                continue

            good_snapshots.append(snapshot)

        print("msg:", "init")

        good_snapshots.sort(key=lambda v: v.get("created_at", 0))

        for snapshot in good_snapshots:
            print("msg:", snapshot["name"][len(snapshot_prefix):])


        # cloud_ip = get_cloud_ip(TEAM)
        # if not cloud_ip:
        #     log_stderr("no cloud ip, exiting")
        #     return 1

        # cmd = ["sudo", "/cloud/scripts/list_snapshots.sh", str(TEAM)]

        # try:
        #     snapshots = subprocess.check_output(["ssh"] + SSH_YA_OPTS + [cloud_ip] + cmd).decode("utf-8")
        # except subprocess.CalledProcessError:
        #     log_stderr("get shapshots list failed")
        #     return 1
        # for line in snapshots.split("\n"):
        #     line = re.sub(r" \([^)]*\)", "", line)
        #     line = re.sub(r"Name: ", "", line)
        #     line = re.sub(r"This machine does not have any snapshots", "no snapshots are created yet", line)
        #     if not line.strip():
        #         continue
        #     print("msg:", line)
        # print(snapshots)
    return 0

    
if __name__ == "__main__":
    sys.stdout = os.fdopen(1, 'w', 1)
    print("started: %d" % time.time())
    exitcode = 1
    try:
        os.chdir(os.path.dirname(os.path.realpath(__file__)))
        exitcode = main()
    except:
        traceback.print_exc()
    print("exit_code: %d" % exitcode)
    print("finished: %d" % time.time())
