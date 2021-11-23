#!/bin/bash
H=proctf-21-local-dev
D=$(dirname $0)
set -ex
scp $H:/home/builder/development/rtems/kernel/rtems/testsuites/samples/hello/init.c src
scp $H:/home/builder/development/rtems/kernel/lm32/run.sh        .
scp $H:/home/builder/development/rtems/kernel/lm32/debug.sh      .
scp $H:/home/builder/development/rtems/kernel/lm32/save-slots.sh deploy
git status
git diff
