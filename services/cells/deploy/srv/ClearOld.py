#!/usr/bin/env python3
import time,os,shutil
from stat import S_ISREG, ST_CTIME, ST_MODE
import datetime

def CleanOld(dirpath,last_time):
    for fn in os.listdir(dirpath):
        pth = os.path.join(dirpath,fn)
        stat = os.stat(pth)
        curtime = datetime.datetime.now()
        if os.path.isdir(pth):
            ct = datetime.datetime.fromtimestamp(stat[ST_CTIME])
            if curtime - ct > last_time:
                print("Removing",pth)
                shutil.rmtree(pth)
    return

while 1:
    CleanOld("data",datetime.timedelta(minutes=30))
    time.sleep(60)
