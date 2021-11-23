#!/bin/sh

chown -R fs:fs /home/fs

./gen.keys.py

export PYTHONUNBUFFERED=1
exec gunicorn -w 8 fs:app -b 0.0.0.0:7777 -u fs -g fs --capture-output --timeout=45
