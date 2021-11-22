#!/bin/sh

export PYTHONUNBUFFERED=1
./ClearOld.py &
exec gunicorn -w 8 wsgi:app -b 0.0.0.0:5000 -u cells -g cells --capture-output --timeout=45
