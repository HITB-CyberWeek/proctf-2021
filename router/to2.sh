#!/bin/bash
echo "$(date) Switching to uplink 2"
cp -v uplink2.yaml /etc/netplan/01-ctf.yaml
netplan apply
conntrack -F
ip ro sh | grep default
