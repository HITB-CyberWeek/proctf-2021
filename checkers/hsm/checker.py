#!/usr/bin/env python3
import hashlib
import logging
import random
import requests
import sys
import traceback

OK, CORRUPT, MUMBLE, DOWN, CHECKER_ERROR = 101, 102, 103, 104, 110

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
    return "".join(random.choice(charset) for _ in range(length))


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
        public = "Got {!r} status code on {!r} request.".format(response.status_code, url)
        verdict(verdict_on_http_error, public=public)
    return response


class Client:
    def __init__(self, host: str, port: int, oauth: str = None, verdict_on_http_error: int = MUMBLE):
        self.base_url = "https://{}:{}".format(host, port)
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
        logging.info("Got response: %r.", text)
        return text

    def post(self, url_suffix: str, **kwargs):
        url = self.url(url_suffix)
        json = dict(**kwargs)
        logging.info("Sending POST %r: %r ...", url, json)
        response = self.session.post(url, timeout=HTTP_TIMEOUT, json=json)
        text = assert_no_http_error(response, self.verdict_on_http_error, url).text
        logging.info("Got response: %r.", text)
        return text

    def register(self, username: str, password: str):
        return self.post("/register", username=username, password=password)

    def login(self, username, password):
        return self.post("/login", username=username, password=password)

    def generate(self):
        resp = self.post("/generate")
        tokens = resp.split(" ")
        if len(tokens) != 2:
            verdict(MUMBLE, public="Generate returned wrong data")
        return tokens  # slot, pubkey

    def decrypt(self, ciphertext: str):
        return self.post("/decrypt", ciphertext=ciphertext)

    def set_meta(self, meta: str):
        return self.post("/meta", meta=meta)

    def get_meta(self):
        return self.get("/meta")

    def get_plaintext(self):
        return self.get("/plaintext")


def make_password(flag_id: str):
    salt = "9cf53e9d-5f05-42c3-a04a-20b07be2b5fb"
    charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
    digest = hashlib.sha256((salt + flag_id).encode()).digest()
    return "".join(charset[b % len(charset)] for b in digest[:PASSWORD_LENGTH])


def make_plaintext(flag: str):
    return "Hello, Mr. John Doe! Did you know that " + flag + "?"


def get_oauth():
    if OAUTH_LOCAL:
        oauth = "FAKE_OAUTH"  # FIXME: implement as a backup? Separate service for teams will be required.
    else:
        c = Client(OAUTH_SERVER_HOST, OAUTH_SERVER_PORT, verdict_on_http_error=CHECKER_ERROR)
        oauth = c.get("/")  # FIXME: implement it!
    # FIXME: add token caching?
    logging.info("Got new OAuth token: %r.", oauth)
    return oauth


def encrypt(flag, pubkey):
    return "FIXME:" + flag + ":" + pubkey


def check(host):
    c = Client(host, SERVICE_PORT, get_oauth())
    c.get("/")
    verdict(OK)


def put(host, flag_id, flag, vuln):
    c = Client(host, SERVICE_PORT, get_oauth())

    c.register(username=flag_id, password=make_password(flag_id))

    slot, pubkey = c.generate()
    c.set_meta(flag_id)

    plaintext = make_plaintext(flag)
    ciphertext = encrypt(plaintext, pubkey)  # Local encryption

    c.decrypt(ciphertext)
    remote_plaintext = c.get_plaintext()
    if remote_plaintext != plaintext:
        verdict(MUMBLE, public="Wrong decryption result")

    remote_meta = c.get_meta()
    if remote_meta != flag_id:
        verdict(MUMBLE, public="Corrupted meta-information")

    verdict(OK, "{}:{}".format(slot, flag_id))  # Slot is helpful for exploitation


def get(host, flag_id, flag, vuln):
    slot, flag_id = flag_id.split(":")

    c = Client(host, SERVICE_PORT, get_oauth())
    c.login(username=flag_id, password=make_password(flag_id))

    remote_plaintext = c.get_plaintext()
    if flag not in remote_plaintext:
        verdict(MUMBLE, public="Flag not found in plaintext")

    plaintext = make_plaintext(flag)
    if remote_plaintext != plaintext:
        verdict(MUMBLE, public="Plaintext was tampered with")

    verdict(OK, "Flag found")


def main(args):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")

    cmd_mapping = {
        "info": (info, 0),
        "check": (check, 1),
        "put": (put, 4),
        "get": (get, 4),
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