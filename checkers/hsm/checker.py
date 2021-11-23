#!/usr/bin/env python3
import hashlib
import logging
import os
import random
import string

import requests
import subprocess
import sys
import traceback

OK, CORRUPT, MUMBLE, DOWN, CHECKER_ERROR = 101, 102, 103, 104, 110

SERVICE_PROTO = "http"  # FIXME: change to https!
SERVICE_PORT = 9000
HTTP_TIMEOUT = 10
PASSWORD_LENGTH = 12
OAUTH_LOCAL = True  # True if generate locally, False if make request to remote OAuth service
OAUTH_SERVER_PORT = 8080
OAUTH_SERVER_HOST = "localhost"
MAX_SLOTS = 17*30  # keep in sync with init.c!


class ProtocolViolationError(Exception):
    pass


def gen_str(charset: str, length: int):
    return "".join(random.choices(charset, k=length))


def verdict(exit_code, public="", private=""):
    if private:
        logging.error(private)
    if public:
        logging.info("Public verdict: %r.", public)
        print(public)
    logging.info("Exit with code: %d.", exit_code)
    sys.exit(exit_code)


def info():
    verdict(OK, "vulns: 1")


def assert_no_http_error(response: requests.Response, verdict_on_http_error: int, url: str = None):
    if response.status_code != 200:
        logging.error("Error %d, response: %r.", response.status_code, response.text)
        public = "Got {!r} status code on {!r} request.".format(response.status_code, url)
        verdict(verdict_on_http_error, public=public)
    return response


class Client:
    def __init__(self, host: str, port: int, oauth: str = None, verdict_on_http_error: int = MUMBLE):
        self.base_url = "{}://{}:{}".format(SERVICE_PROTO, host, port)
        self.session = requests.Session()
        self.verdict_on_http_error = verdict_on_http_error
        if oauth is not None:
            self.session.headers["RateLimitingToken"] = oauth

    def url(self, suffix: str):
        return self.base_url + suffix

    def get(self, url_suffix: str):
        url = self.url(url_suffix)
        logging.info("Sending GET %r ...", url)
        response = self.session.get(url, timeout=HTTP_TIMEOUT)
        text = assert_no_http_error(response, self.verdict_on_http_error, url).text
        logging.info("Success, response: %r.", text)
        return text

    def post(self, url_suffix: str, **kwargs):
        url = self.url(url_suffix)
        logging.info("Sending POST %r: %r ...", url, kwargs)
        response = self.session.post(url, timeout=HTTP_TIMEOUT, data=kwargs)
        text = assert_no_http_error(response, self.verdict_on_http_error, url).text
        logging.info("Success, response: %r.", text)
        return text

    def register(self, username: str, password: str, token: str):
        return self.post("/register", username=username, password=password, token=token)

    def login(self, username, password):
        return self.post("/login", username=username, password=password)

    def generate(self):
        resp = self.get("/generate")
        tokens = resp.split(" = ")
        if len(tokens) != 2:
            verdict(MUMBLE, public="Generate returned wrong data")
        return tokens  # slot, pubkey

    def decrypt(self, ciphertext: str):
        return self.post("/decrypt", ciphertext=ciphertext)

    def set_meta(self, meta: str):
        return self.post("/setmeta", meta=meta)

    def get_meta(self):
        return self.get("/getmeta")

    def get_plaintext(self):
        return self.get("/getplaintext")


def make_password(flag_id: str, length: int = PASSWORD_LENGTH):
    salt = "9cf53e9d-5f05-42c3-a04a-20b07be2b5fb"
    charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    digest = hashlib.sha256((salt + flag_id).encode()).digest()
    return "".join(charset[b % len(charset)] for b in digest[:length])


def make_meta(flag_id: str):
    long_meta = make_password(flag_id + "aa", length=64) + make_password(flag_id + "bb", length=64)
    long_meta = long_meta[:33]
    if len(long_meta) != 33:
        raise ValueError("Invalid meta length: {!r}".format(long_meta))
    return long_meta


def get_oauth():
    if OAUTH_LOCAL:
        oauth = "FAKE_OAUTH"  # FIXME: implement as a backup? Separate service for teams will be required.
    else:
        c = Client(OAUTH_SERVER_HOST, OAUTH_SERVER_PORT, verdict_on_http_error=CHECKER_ERROR)
        oauth = c.get("/")  # FIXME: implement it!
    # FIXME: add token caching?
    logging.info("Got new OAuth token: %r.", oauth)
    return oauth


def encrypt(plaintext, pubkey_hex):
    logging.info("Encrypting %r with pubkey %r ...", plaintext, pubkey_hex)
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = "."
    proc = subprocess.Popen(["./encrypt", pubkey_hex, plaintext], stdout=subprocess.PIPE, env=env)
    stdout, _ = proc.communicate()
    ciphertext = stdout.decode().strip()
    logging.info("Ciphertext: %r.", ciphertext)
    return ciphertext


def check(host):
    c = Client(host, SERVICE_PORT, get_oauth())
    if "To use Cloud HSM Service, you must:" in c.get("/"):
        verdict(OK)
    else:
        verdict(MUMBLE, public="Prompt not found")


def put(host, flag_id, flag, vuln):
    flag_id = flag_id.replace("-", "")

    c = Client(host, SERVICE_PORT, get_oauth())
    c.register(username=flag_id, password=make_password(flag_id), token="nonce")

    slot, pubkey = c.generate()
    long_meta = make_meta(flag_id)  # Important to check all 33 chars!
    c.set_meta(long_meta)

    remote_meta = c.get_meta()
    if remote_meta != long_meta:
        verdict(MUMBLE, public="Corrupted meta-information")

    plaintext = flag
    ciphertext = encrypt(flag, pubkey)  # Local encryption

    c.decrypt(ciphertext)
    remote_plaintext = c.get_plaintext()
    if remote_plaintext != plaintext:
        verdict(MUMBLE, public="Wrong decryption result")

    verdict(OK, "{}:{}".format(slot, flag_id))  # Slot is helpful for exploitation


def get(host, flag_id, flag, vuln):
    slot, flag_id = flag_id.split(":")

    c = Client(host, SERVICE_PORT, get_oauth())
    c.login(username=flag_id, password=make_password(flag_id))

    remote_plaintext = c.get_plaintext()
    if flag != remote_plaintext:
        verdict(MUMBLE, public="Flag not found in plaintext")

    verdict(OK, "Flag found")


def exploit(host, slot):
    credentials_filename = "sploit.credentials.txt"
    c = Client(host, SERVICE_PORT, get_oauth())
    try:
        with open(credentials_filename) as f:
            username, password = f.readline().strip().split(":")
        c.login(username, password)
    except FileNotFoundError:
        username = gen_str(charset=string.ascii_lowercase + string.digits, length=12)
        password = make_password(username)
        c.register(username, password, get_oauth())
        with open(credentials_filename, "w") as f:
            f.writelines([username + ":" + password])
    c.generate()
    # c.set_meta(gen_str())
    raise NotImplementedError()


def main(args):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

    cmd_mapping = {
        "info":     (info, 0),
        "check":    (check, 1),
        "put":      (put, 4),
        "get":      (get, 4),
        "exploit":  (exploit, 2),
    }

    if not args:
        verdict(CHECKER_ERROR, "No args", "No args")

    cmd, args = args[0], args[1:]
    if cmd not in cmd_mapping:
        verdict(CHECKER_ERROR, "Checker error", "Wrong command %s" % cmd)

    handler, args_count = cmd_mapping[cmd]
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
