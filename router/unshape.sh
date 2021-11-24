#!/bin/bash
if [ -z "$1" ]; then
	echo "Usage: $(basename $0) <VLAN_NUMBER>"
	exit 1
fi

set -ex
tc qdisc del dev vlan.$1 root
