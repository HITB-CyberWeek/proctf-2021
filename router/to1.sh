#!/bin/bash
echo "$(date) Switching to uplink 1"
cp -v uplink1.yaml /etc/netplan/01-ctf.yaml
netplan apply
conntrack -F
ip ro sh | grep default
