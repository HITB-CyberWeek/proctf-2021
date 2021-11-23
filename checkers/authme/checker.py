#!/usr/bin/env python3

import sys
import socket
import hashlib
import random
import re
import functools
import time
import json
import pathlib
import base64
import traceback

OK, CORRUPT, MUMBLE, DOWN, CHECKER_ERROR = 101, 102, 103, 104, 110

PORT = 3256
TIMEOUT = 10

ABC = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"


class ProtocolViolationError(Exception):
    pass


def verdict(exit_code, public="", private=""):
    if public:
        print(public)
    if private:
        print(private, file=sys.stderr)
    sys.exit(exit_code)


def info():
    verdict(OK, "vulns: 1\npublic_flag_description: Flag ID is user name, flag is flag\n")



def send_pkt(s, data):
    s.sendall(bytes([len(data)]) + data)

def recv_pkt(s):
    size_byte = s.recv(1)
    if len(size_byte) == 0:
        return b""
    size = size_byte[0]

    pkt = bytearray()
    while len(pkt) < size:
        data = s.recv(size - len(pkt))
        if not data:
            raise ProtocolViolationError("server closed connection in the middle of the packet")
        pkt += data
    return bytes(pkt)


def check(host):
    s = socket.socket()
    s.settimeout(TIMEOUT)
    s.connect((host, PORT))

    verdict(OK)


def put(host, flag_id, flag, vuln):
    s = socket.socket()
    s.settimeout(TIMEOUT)
    s.connect((host, PORT))

    send_pkt(s, b"\x00")
    send_pkt(s, flag_id.encode())

    password = "".join(random.choice(ABC) for i in range(random.randrange(10, 12)))
    send_pkt(s, password.encode())
    send_pkt(s, flag.encode())

    pkt = recv_pkt(s)

    if pkt != b'\x00':
        verdict(MUMBLE, "Failed to register", "Failed to register: %s %s %s" % (flag_id, flag, pkt))

    verdict(OK, json.dumps({"public_flag_id": flag_id, "password": password}))


def get(host, flag_id, flag, vuln):
    try:
        info = json.loads(flag_id)
        flag_id = info["public_flag_id"]
        password = info["password"]
    except Exception:
        verdict(CHECKER_ERROR, "Bad flag id", "Bad flag_id: %s" % traceback.format_exc())

    s = socket.socket()
    s.settimeout(TIMEOUT)
    s.connect((host, PORT))

    send_pkt(s, b"\x02")

    while True:
        login = recv_pkt(s)
        if not login:
            verdict(MUMBLE, "Bad users listing", "User is not in users list: %s" % flag_id)

        if flag_id.encode() == login:
            break
    s.close()

    s = socket.socket()
    s.settimeout(TIMEOUT)
    s.connect((host, PORT))

    send_pkt(s, b"\x01")
    send_pkt(s, flag_id.encode())

    server_random = recv_pkt(s)
    client_random = ("".join(random.choice(ABC) for i in range(random.randrange(2, 6)))).encode()

    send_pkt(s, client_random)

    our_random_hash = hashlib.sha256(server_random + client_random).digest()
    password_hash = hashlib.sha256(password.encode()).digest()

    response = pow(int.from_bytes(password_hash[-8:], "little"),
                   int.from_bytes(our_random_hash[-8:], "little"),
                   256**8)
    send_pkt(s, int.to_bytes(response, 8, "little"))

    got_flag = recv_pkt(s)

    if flag.encode() != got_flag:
        verdict(CORRUPT, "No such flag",
            "No such flag %s, got %s" % (flag, got_flag))

    verdict(OK, flag_id)


def main(args):
    CMD_MAPPING = {
        "info": (info, 0),
        "check": (check, 1),
        "put": (put, 4),
        "get": (get, 4),
    }

    if not args:
        verdict(CHECKER_ERROR, "No args", "No args")

    cmd, args = args[0], args[1:]
    if cmd not in CMD_MAPPING:
        verdict(CHECKER_ERROR, "Checker error", "Wrong command %s" % cmd)

    handler, args_count = CMD_MAPPING[cmd]
    if len(args) != args_count:
        verdict(CHECKER_ERROR, "Checker error", "Wrong args count for %s" % cmd)

    try:
        handler(*args)

    except ProtocolViolationError as E:
        verdict(MUMBLE, "Protocol violation", "Protocol violation: %s" % traceback.format_exc())
    except ConnectionRefusedError as E:
        verdict(DOWN, "Connect refused", "Connect refused: %s" % E)
    except ConnectionError as E:
        verdict(MUMBLE, "Connection aborted", "Connection aborted: %s" % E)
    except OSError as E:
        verdict(DOWN, "Connect error", "Connect error: %s" % E)
    except Exception as E:
        verdict(CHECKER_ERROR, "Checker error", "Checker error: %s" % traceback.format_exc())
    verdict(CHECKER_ERROR, "Checker error", "No verdict")


if __name__ == "__main__":
    main(args=sys.argv[1:])
