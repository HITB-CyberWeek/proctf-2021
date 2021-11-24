#!/bin/bash
while true; do
	echo "$(date) Sleeping..."
	sleep 300
	echo "$(date) Switching to uplink 2"
	cp -v uplink2.yaml /etc/netplan/01-ctf.yaml
	netplan apply
	conntrack -F
	ip ro sh | grep default
	echo

	echo "$(date)Sleeping..."
	sleep 300
	echo "$(date) Switching to uplink 1"
	cp -v uplink1.yaml /etc/netplan/01-ctf.yaml
	netplan apply
	conntrack -F
	ip ro sh | grep default
	echo
done
