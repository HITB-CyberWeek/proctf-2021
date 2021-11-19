#!/bin/bash

cd "$(dirname "$0")"

mkdir -p data
chown root:root . data authme Dockerfile docker-compose.yaml start.sh

touch data/flags.txt
chattr -a data/flags.txt
chown authme:authme data/flags.txt
chmod 600 data/flags.txt
chattr +a data/flags.txt

ulimit -c 0

runuser -u authme ./authme
