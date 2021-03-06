#!/bin/bash

set -e

cd chromedriver && \
docker build -f Dockerfile.build -t p0ck37/chromedriver-build . && \
docker run -v "${PWD}:/build" p0ck37/chromedriver-build && \
cd ..

if [ -d .deploy ]; then rm -Rf .deploy; fi
mkdir .deploy

cp docker-compose.yml .deploy/

mkdir .deploy/chromedriver
cp chromedriver/{wrapper,Dockerfile,start.sh,chrome.cron} .deploy/chromedriver/

mkdir .deploy/web
cp -r web/{Dockerfile,app.js,package.json,views,server.crt} .deploy/web/

mkdir .deploy/cron
cp -r cron/{Dockerfile,p0ck37.cron} .deploy/cron/
