#!/usr/bin/python3

import sys
import os
import secrets
import hashlib

N = 64

def gentoken(team, n=32):
 abc = "abcdef0123456789"
 return "OAUTH_" + str(team) + "_" + "".join([secrets.choice(abc) for i in range(n)])

os.chdir(os.path.dirname(os.path.realpath(__file__)))

try:
    os.mkdir("tokens")
except FileExistsError:
    print("Remove ./tokens dir first")
    sys.exit(1)

for i in range(1, N+1):
    token = gentoken(i)
    open("tokens/%d.txt" % i, "w").write(token + "\n")
