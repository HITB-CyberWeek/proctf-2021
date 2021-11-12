#!/bin/bash

cd "$(dirname "$0")"

mkdir -p data
chown root:root . data chess Dockerfile docker-compose.yaml start.sh

touch data/flags.txt
chattr -a data/flags.txt
chown chess:chess data/flags.txt
chmod 600 data/flags.txt
chattr +a data/flags.txt

ulimit -c 0

exec socat TCP-LISTEN:3255,reuseaddr,fork system:'stdbuf -i0 -e0 -o0 ./chess',su=chess
