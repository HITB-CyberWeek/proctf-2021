# Developed by Alexander Bersenev from Hackerdom team, bay@hackerdom.ru

"""Common functions and consts that are often used by other scripts in 
this directory"""

import subprocess
import sys
import time
import os
import shutil

DOMAIN = "ctf.hitb.org"

# change me before the game
ROUTER_HOST = "vpn.ctf.hitb.org"

SSH_OPTS = [
    "-o", "StrictHostKeyChecking=no",
    "-o", "CheckHostIP=no",
    "-o", "NoHostAuthenticationForLocalhost=yes",
    "-o", "BatchMode=yes",
    "-o", "LogLevel=ERROR",
    "-o", "UserKnownHostsFile=/dev/null",
    "-o", "ConnectTimeout=10"
]

SSH_DO_OPTS = SSH_OPTS + [
    "-o", "Port=2222",
    "-o", "User=root",
    "-o", "IdentityFile=hitb2021_do_deploy"
]

SSH_YA_OPTS = SSH_OPTS + [
    "-o", "User=cloud",
    #"-o", "IdentityFile=ructfe2020_ya_deploy"
]

# def untake_cloud_ip(team):
#     for slot in os.listdir("db/team%d" % team):
#         if not slot.startswith("slot_"):
#             continue
#         os.rename("db/team%d/%s" % (team, slot), "slots/%s" % slot)
    
#     try:
#         os.remove("db/team%d/cloud_ip" % team)
#     except FileNotFoundError:
#         return


# def take_cloud_ip(team):
#     for slot in os.listdir("db/team%d" % team):
#         if not slot.startswith("slot_"):
#             continue
#         shutil.copy2("db/team%d/%s" % (team, slot), "db/team%d/cloud_ip" % team)
#         cloud_ip = open("db/team%d/cloud_ip" % team).read().strip()
#         print("Retaking slot %s, taken %s" % (slot, cloud_ip), file=sys.stderr)
#         return cloud_ip

#     for slot in os.listdir("slots"):
#         try:
#             os.rename("slots/%s" % slot, "db/team%d/%s" % (team, slot))
#         except FileNotFoundError:
#             continue

#         shutil.copy2("db/team%d/%s" % (team,slot), "db/team%d/cloud_ip" % team)
#         cloud_ip = open("db/team%d/cloud_ip" % team).read().strip()
#         print("Taking slot %s, taken %s" % (slot, cloud_ip), file=sys.stderr)
#         return cloud_ip
#     return None


# def get_cloud_ip(team):
#     try:
#         return open("db/team%d/cloud_ip" % team).read().strip()
#     except FileNotFoundError as e:
#         return None


def log_progress(*params):
    print("progress:", *params, flush=True)


def call_unitl_zero_exit(params, redirect_out_to_err=True, attempts=60, timeout=10):
    if redirect_out_to_err:
        stdout = sys.stderr
    else:
        stdout = sys.stdout

    for i in range(attempts-1):
        if subprocess.call(params, stdout=stdout) == 0:
            return True
        time.sleep(timeout)
    if subprocess.call(params, stdout=stdout) == 0:
        return True

    return None

def get_available_vms():
    try:
        ret = {}
        for line in open("%s/vms.txt" % DB_PATH):
            if line.strip().startswith("#"):
                continue
            vm, vm_number = line.rsplit(maxsplit=1)
            ret[vm] = int(vm_number)
        return ret
    except (OSError, ValueError):
        return {}

def get_vm_name_by_num(num):
    if list(get_available_vms().values()).count(num) != 1:
        return ""

    for k, v in get_available_vms().items():
        if v == num:
            return k
    return ""
