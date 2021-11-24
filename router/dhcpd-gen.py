#!/usr/bin/env python3
import sys

print("""# Cyberweek CTF dhcp server config

option domain-name "ctf.local";
option domain-name-servers 8.8.8.8, 8.8.4.4;

default-lease-time 36000;  # 10h
max-lease-time 72000;      # 20h

ddns-update-style none;
""")

for n in list(range(101, 119)) + [199]:
    print("""
subnet 192.168.{n}.0 netmask 255.255.255.0 {{
  range 192.168.{n}.100 192.168.{n}.150;
  option subnet-mask 255.255.255.0;
  option routers 192.168.{n}.1;
}}
""".format(n=n))
    print("vlan.{} ".format(n), end="", file=sys.stderr)

print("", file=sys.stderr)
