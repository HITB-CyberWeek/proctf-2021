#!/bin/bash

rm -f /tmp/.X99-lock
export DISPLAY=:99
Xvfb :99 -screen 0 1366x768x16 -nolisten tcp -nolisten unix &

/usr/local/bin/wrapper
