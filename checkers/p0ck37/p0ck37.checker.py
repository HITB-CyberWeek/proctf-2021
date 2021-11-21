#!/usr/bin/env python3
  
import sys
import uuid
import traceback
import json
import hashlib
import requests
import io
import pdfplumber
requests.packages.urllib3.disable_warnings()
from urllib.parse import urlparse, urljoin, parse_qs
from checker_helper import *

PORT = 3000
TIMEOUT = 10
OAUTH_TOKEN = 'd7ae69cd-7e91-44de-8729-12cded47b3f2'
OAUTH_ENDPOINT = 'https://auth.ctf.hitb.org:5000/'
FLAGS_API_KEY = '25807689-9ae1-4894-a6f8-940abd1c3a4a'
FLAGS_ENDPOINT = 'http://jury-p0ck37.ctf.hitb.org:8080/'

def info():
    verdict(OK, "vulns: 1\npublic_flag_description: Flag ID is the ID of a user who has a flag")

def check(args):
    if len(args) != 1:
        verdict(CHECKER_ERROR, "Checker error", "Wrong args count for check()")
    host = args[0]
    trace("check(%s)" % host)

    verdict(OK)

def login(host, user_name):
    p0ck37_url = f"http://{host}:{PORT}/"
    try:
        r = requests.get(f"http://{host}:{PORT}/", timeout=TIMEOUT, verify=False)
    except requests.exceptions.ConnectionError as e:
        verdict(DOWN, "Connection error", "Connection error during login: %s" % e)
    except requests.exceptions.Timeout as e:
        verdict(DOWN, "Timeout", "Timeout during login: %s" % e)

    if not r.url.startswith(urljoin(OAUTH_ENDPOINT, "/account/login")):
        verdict(MUMBLE, "Unexpected OAuth2 endpoint", "Unexpected OAuth2 endpoint: '%s'" % r.url)

    query = parse_qs(urlparse(r.url).query)

    if "ReturnUrl" not in query:
        verdict(MUMBLE, "Bad login parameters", "Can't find 'ReturnUrl' parameter in '%s'" % r.url)

    if len(query["ReturnUrl"]) != 1:
        verdict(MUMBLE, "Bad login parameters", "Multiple 'ReturnUrl' in '%s'" % r.url)

    return_url = query["ReturnUrl"][0]
    # TODO check redirect_uri in return_url

    login_data = {"ReturnUrl": return_url, "Username": user_name, "Token": OAUTH_TOKEN}
    session = requests.Session()
    r = session.post(urljoin(OAUTH_ENDPOINT, "/account/login"), data=login_data, verify=False)

    return session

def add_link(host, link, session):
    p0ck37_url = f"http://{host}:{PORT}/"
    try:
        r = session.get(urljoin(p0ck37_url, "/add"), params={"link": link}, timeout=TIMEOUT)
    except requests.exceptions.ConnectionError as e:
        verdict(DOWN, "Connection error", "Connection error during link publishing: %s" % e)
    except requests.exceptions.Timeout as e:
        verdict(DOWN, "Timeout", "Timeout during link publishing: %s" % e)

    if r.status_code != 200:
        verdict(MUMBLE, "Can't add new link", "Can't add new link: '%s'" % r.text)
    #print(r.text)

def register_flag(flag):
    headers = {"x-api-key": FLAGS_API_KEY}
    data = {"flag": flag}
    r = requests.post(urljoin(FLAGS_ENDPOINT, "/urls"), headers=headers, json=data)
    if r.status_code != 200:
        verdict(CHECKER_ERROR, "Checker error", "Error during flag publishing: %s" % r.text)

    if "id" not in r.json():
        verdict(CHECKER_ERROR, "Checker error", "Can't find 'id' in response: '%s'" % r.text)

    return r.json()['id']

def put(args):
    if len(args) != 4:
        verdict(CHECKER_ERROR, "Checker error", "Wrong args count for put()")
    host, flag_id, flag_data, vuln = args
    trace("put(%s, %s, %s, %s)" % (host, flag_id, flag_data, vuln))

    secret_flag_id = register_flag(flag_data)
    secret_flag_url = urljoin(FLAGS_ENDPOINT, f"/{secret_flag_id}")

    user_name = str(uuid.uuid4())

    session = login(host, user_name)
    add_link(host, secret_flag_url, session)

    p0ck37_user_id = hashlib.md5(f"{user_name}{OAUTH_TOKEN}".encode()).hexdigest()
    # TODO add additional fields for saving
    flag_id = json.dumps({"public_flag_id": p0ck37_user_id, "user_name": user_name, "secret_flag_id": secret_flag_id})
    verdict(OK, flag_id)

def get(args):
    if len(args) != 4:
        verdict(CHECKER_ERROR, "Checker error", "Wrong args count for get()")
    host, flag_id, flag_data, vuln = args
    trace("get(%s, %s, %s, %s)" % (host, flag_id, flag_data, vuln))

    info = json.loads(flag_id)

    session = login(host, info["user_name"])

    p0ck37_url = f"http://{host}:{PORT}/"
    # TODO check if page contains link to flag

    p0ck37_download_url = urljoin(p0ck37_url, f"/download/{info['secret_flag_id']}.pdf")

    try:
        r = session.get(p0ck37_download_url, timeout=TIMEOUT)
    except requests.exceptions.ConnectionError as e:
        verdict(DOWN, "Connection error", "Connection error during link publishing: %s" % e)
    except requests.exceptions.Timeout as e:
        verdict(DOWN, "Timeout", "Timeout during link publishing: %s" % e)

    if r.status_code != 200:
        verdict(MUMBLE, "Can't download file", "Can't download file: '%s'" % r.text)

    with pdfplumber.open(io.BytesIO(r.content)) as pdf:
        page = pdf.pages[0]
        text = page.extract_text()
        if flag_data not in text:
            verdict(CORRUPT, "Can't find flag in pdf", "Can't find flag in pdf")

    verdict(OK)

def main(args):
    if len(args) == 0:
        verdict(CHECKER_ERROR, "Checker error", "No args")
    try:
        if args[0] == "info":
            info()
        elif args[0] == "check":
            check(args[1:])
        elif args[0] == "put":
            put(args[1:])
        elif args[0] == "get":
            get(args[1:])
        else:
            verdict(CHECKER_ERROR, "Checker error", "Wrong action: " + args[0])
    except Exception as e:
        verdict(CHECKER_ERROR, "Checker error", "Exception: %s" % traceback.format_exc())

if __name__ == "__main__":
    try:
        main(sys.argv[1:])
        verdict(CHECKER_ERROR, "Checker error", "No verdict")
    except Exception as e:
        verdict(CHECKER_ERROR, "Checker error", "Exception: %s" % e)
