#!/bin/sh

chown -R cells:cells .
chmod +x cells.elf
chmod a+r static
chmod a+r templates

export PYTHONUNBUFFERED=1
./ClearOld.py &
exec gunicorn -w 8 wsgi:app -b 0.0.0.0:5000 -u cells -g cells --capture-output --timeout=45
