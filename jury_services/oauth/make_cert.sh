#!/bin/bash

openssl req -new -newkey rsa:4096 -days 3650 -nodes -x509 -subj "/CN=auth.ctf.hitb.org" -keyout server.key -out server.crt
openssl pkcs12 -export -out server.pfx -inkey server.key -in server.crt -passout pass:
