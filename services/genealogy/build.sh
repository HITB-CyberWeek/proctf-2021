#!/bin/bash

set -ex

shopt -s globstar

docker build -f Dockerfile.build -t genealogy-build .
docker run -v "${PWD}/src:/src" genealogy-build

if [ -d .deploy ]; then rm -Rf .deploy; fi
mkdir .deploy

cp -r src .deploy/

rm -rf .deploy/src/include
rm -rf .deploy/src/brotobuf/*.cpp

rm -rf .deploy/src/**/*.o
rm -rf .deploy/src/keys
rm -rf .deploy/src/.gitignore
rm -rf .deploy/src/.depend
mv .deploy/src/genealogy .deploy/

cp docker-compose.yaml .deploy/
cp Dockerfile .deploy/
cp -r data .deploy/
cp -r env .deploy/
