#!/bin/bash

export DISPLAY=:99
Xvfb :99 -screen 0 1366x768x16 2>/dev/null &

/usr/local/bin/wrapper 2>/dev/null
