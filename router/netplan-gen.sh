#!/bin/bash
set -e
CFG=/etc/netplan/01-ctf.yaml
python3 netplan-gen.py > $CFG
echo "Generated: '$CFG'"
echo "Now you may want to run: 'netplan apply'"
