#!/bin/bash
if [ -z "$1" ]; then
	echo "Usage: $(basename $0) <VLAN_NUMBER>"
	exit 1
fi

set -ex
tc qdisc add dev vlan.$1 root tbf rate 150mbit burst 300mbit latency 900ms
