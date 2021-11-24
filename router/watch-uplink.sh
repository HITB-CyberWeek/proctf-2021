#!/bin/bash
while true; do
    for i in 1 2; do
    	if ip ro sh | grep default | grep vlan.20$i; then
    		echo
    		echo "Using : UPLINK $i"
    		if ping 8.8.8.8 -c1 >/dev/null 2>&1; then 
    			echo "Status: OK"
    		else
    			echo "Status: PROBLEM"
    		fi
    	fi
    done
done
