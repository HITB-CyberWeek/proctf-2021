#!/bin/bash
if [ -z "$2" ]; then
    echo "Usage: $(basename $0) HOST SLOT"
    exit 1
fi
set -ex
cd ../../checkers/hsm
./checker.py exploit $1 $2
