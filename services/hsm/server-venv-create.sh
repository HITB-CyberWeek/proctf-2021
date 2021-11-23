#!/bin/bash
set -ex
python3.7 -m venv venv
venv/bin/python3.7 -m pip install -r requirements.txt
echo Done.
