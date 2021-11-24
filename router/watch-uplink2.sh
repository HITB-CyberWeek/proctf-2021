#!/bin/bash
IP=192.168.1.1
while true; do echo -n `date`" [UPLINK 2: $IP] "; echo `timeout 1 ping $IP -c1 | grep received`; sleep 1; done
