#!/bin/bash

host=$1

count=50
for i in $(seq $count); do
    echo $i

    flag=$(uuidgen)
    put=$(./p0ck37.checker.py put $host id1 $flag 1)
    exit_code=$?
    echo $put

    if [ $exit_code -ne 101 ]; then
        echo "EXIT CODE: $exit_code"
        continue
    fi

    ./p0ck37.checker.py get $host "$put" $flag 1
    exit_code=$?

    if [ $exit_code -ne 101 ]; then
        echo "EXIT CODE: $exit_code"
    fi

    echo ""
done
