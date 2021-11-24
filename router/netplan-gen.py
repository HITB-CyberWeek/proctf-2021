#!/usr/bin/env python3

print("""
network:
  version: 2
  ethernets:
    enp3s0:
      dhcp4: false
  vlans:
""".lstrip("\n"))

# teams
for n in range(101, 119):
    print("""
    vlan.{n}:    # team {n}
      id: {n}
      link: enp3s0
      addresses: [192.168.{n}.1/24]""".format(n=n).lstrip("\n"))

print("""
    vlan.199:     # jury
      id: 199
      link: enp3s0
      addresses: [192.168.199.1/24]

    vlan.201:     # uplink 1
      optional: true
      id: 201
      link: enp3s0
      dhcp4: true

    vlan.202:     # uplink 2
      optional: true
      id: 202
      link: enp3s0
      dhcp4: true
      dhcp4-overrides:
        use-routes: false
""".lstrip("\n"))

