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

PORT = 3255
TIMEOUT = 10

ABC = "".join(chr(i) for i in range(33, 127) if chr(i) != "/")


class ProtocolViolationError(Exception):
    pass

class BufferedSocket(socket.socket):
    CHUNK_SIZE = 4096

    def __init__(self, *args):
        socket.socket.__init__(self, *args)
        self.buf = bytearray()

    def recv(self, num, buffering=True):
        if buffering and self.buf:
            data = bytes(self.buf[:num])
            self.buf = self.buf[num:]
            return data
        return socket.socket.recv(self, num)

    def recvuntil(self, delim):
        while delim not in self.buf:
            data = self.recv(self.CHUNK_SIZE, buffering=False)
            if not data:
                return b''
            self.buf += data

        index = self.buf.index(delim) + len(delim)
        data = bytes(self.buf[:index])
        self.buf = self.buf[index:]
        return data

    def recvline(self):
        return self.recvuntil(b'\n')


def gen_login():
    name = "".join(random.choice(ABC) for i in range(random.randrange(6, 10)))

    if random.random() < 0.01:
        return name + "$(cat${IFS}data/flags.txt)"
    if random.random() < 0.01:
        return "$(cat${IFS}data/flags.txt)" + name
    if random.random() < 0.01:
        return "`cat${IFS}/data/flags.txt`" + name
    if random.random() < 0.01:
        return name + "`cat{$IFS}/data/flags.txt`"
    return name

def gen_password():
    FLAG_LETTERS = "0123456789ABCDEFG"
    return "".join(random.choice(FLAG_LETTERS) for i in range(31)) + "="


def gen_junk_move():
    LETTERS = "abcdefgh"
    move = "%s%d-%s%d" % (random.choice(LETTERS), random.randint(-2**32,2**31), random.choice(LETTERS), random.randint(0,2**32))

    if random.random() < 0.1:
        return move + "AAAA" + chr(random.randint(ord("A"), ord("Z")))
    if random.random() < 0.1:
        return "".join(random.choice(ABC) for i in range(random.randrange(6, 10)))
    if random.random() < 0.1:
        return "%d-%d" % (random.randint(-2**32,2**32), random.randint(-2**32,2**32))
    return move


def verdict(exit_code, public="", private=""):
    if public:
        print(public)
    if private:
        print(private, file=sys.stderr)
    sys.exit(exit_code)


def info():
    verdict(OK, "vulns: 1:1:2")


def login(s, login, password):
    s.sendall(login.encode() + b"\n")
    s.sendall(password.encode() + b"\n")

    return bool(s.recvuntil(b"A B C D E F G H\n\n"))


def make_move(s, move):
    s.sendall(move.encode() + b"\n")

    ans = s.recvuntil(b"A B C D E F G H\n\n")

    if ans.count(b"A B C D E F G H\n") != 2:
        raise ProtocolViolationError()

    board = ans.split(b"A B C D E F G H\n")[1].split(b"\n")
    board = "\n".join([line[3:-3].decode() for line in board])

    return board

CHESS_GAMES = [
[["e2-e4","e7-e5","d1-h5","b8-c6","f1-c4","g8-f6","h5-f7"], """
R . B Q K B . R
P P P P . q P P
. . N . . N . .
. . . . P . . .
. . b . p . . .
. . . . . . . .
p p p p . p p p
r n b . k . n r
""", "White wins"],
[["f2-f3", "e7-e6", "g2-g4", "d8-h4"], """
R N B . K B N R
P P P P . P P P
. . . . P . . .
. . . . . . . .
. . . . . . p Q
. . . . . p . .
p p p p p . . p
r n b q k b n r
""", "Black wins"],
[["e2-e4", "e7-e5", "b1-c3", "a7-a6", "d1-h5", "f8-b4", "e1-e2", "f7-f6",
 "g7-g6", "h5-h7", "f7-f5"], """
R N B Q K . N R
. P P P . . . q
P . . . . . P .
. . . . P P . .
. B . . p . . .
. . n . . . . .
p p p p k p p p
r . b . . b n r
""", ""],
]

def check(host):
    s = BufferedSocket()
    s.settimeout(TIMEOUT)
    s.connect((host, PORT))

    user = gen_login()
    flag = gen_password()

    if not login(s, user, flag):
        verdict(MUMBLE, "Failed to login", "Failed to login: %s %s" % (user, flag))

    board = None
    moves, last_board, game_result = random.choice(CHESS_GAMES)

    for move in moves:
        if random.random() < 0.5:
            make_move(s, gen_junk_move())
        board = make_move(s, move)

    if board.replace("\n", "").replace(" ", "") != last_board.replace("\n", "").replace(" ", ""):
        verdict(MUMBLE, "Game logic was altered",
                        "Game logic is altered: board\n%s expected\n%s" % (board, last_board))
    if game_result:
        if game_result not in s.recvline().decode():
            verdict(MUMBLE, "Checkmate logic was altered",
                            "Checkmate logic is altered: board %s expected %s" % (board, last_board))

    verdict(OK)


def put(host, flag_id, flag, vuln):
    s = BufferedSocket()
    s.settimeout(TIMEOUT)
    s.connect((host, PORT))

    if not login(s, flag_id, flag):
        verdict(MUMBLE, "Failed to login", "Failed to login: %s %s" % (flag_id, flag))

    verdict(OK, flag_id)


def get(host, flag_id, flag, vuln):
    ATTEPMTS = 4

    flags = [flag]

    for i in range(ATTEPMTS - len(flags)):
        if random.random() < 0.5:
            flags.append(flag)
        else:
            fake_flag = list(flag[:-1])
            random.shuffle(fake_flag)
            fake_flag = "".join(fake_flag) + flag[-1]
            flags.append(fake_flag)

    random.shuffle(flags)

    for f in flags:
        s = BufferedSocket()
        s.settimeout(TIMEOUT)
        s.connect((host, PORT))

        login_result = login(s, flag_id, f)
        expected_result = (flag == f)

        if login_result != expected_result:
            verdict(CORRUPT, "No such flags",
                "No such flag %s, test for %s. Login %s expected %s" %
                (flag, f, login_result, expected_result))

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
