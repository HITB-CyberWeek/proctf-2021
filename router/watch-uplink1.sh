#!/bin/bash
IP=192.168.2.1
while true; do echo -n `date`" [UPLINK 1: $IP] "; echo `timeout 1 ping $IP -c1 | grep received`; sleep 1; done
