#!/usr/bin/env python3
  
import sys
import uuid
import traceback
import json
import hashlib
import requests
import io
import pdfplumber
import http.client
requests.packages.urllib3.disable_warnings()
from urllib.parse import urlparse, urljoin, parse_qs
from checker_helper import *

PORT = 3000
TIMEOUT = 30
RETRY = 2
OAUTH_TOKEN = 'd7ae69cd-7e91-44de-8729-12cded47b3f2'
OAUTH_ENDPOINT = 'https://auth.ctf.hitb.org/'
FLAGS_API_KEY = '25807689-9ae1-4894-a6f8-940abd1c3a4a'
FLAGS_ENDPOINT = 'http://jury-p0ck37.ctf.hitb.org:8080/'

def info():
    verdict(OK, "vulns: 1\npublic_flag_description: Flag ID is the ID of a user with a flag, the flag is in the user's pdf documents")

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
    except (requests.exceptions.ConnectionError, ConnectionRefusedError, http.client.RemoteDisconnected) as e:
        return (DOWN, "Connection error", "Connection error during login: %s" % e, None)
    except requests.exceptions.Timeout as e:
        return (DOWN, "Timeout", "Timeout during login: %s" % e, None)

    if not r.url.startswith(urljoin(OAUTH_ENDPOINT, "/account/login")):
        return (MUMBLE, "Unexpected OAuth2 endpoint", "Unexpected OAuth2 endpoint: '%s'" % r.url, None)

    query = parse_qs(urlparse(r.url).query)

    if "ReturnUrl" not in query:
        return (MUMBLE, "Bad login parameters", "Can't find ReturnUrl parameter in '%s'" % r.url, None)

    if len(query["ReturnUrl"]) != 1:
        return (MUMBLE, "Bad login parameters", "Multiple ReturnUrl in '%s'" % r.url, None)

    return_url = query["ReturnUrl"][0]
    if not return_url.startswith("/connect/authorize"):
        return (MUMBLE, "Bad login parameters", "ReturnUrl does not start with '/connect/authorize' in '%s'" % r.url, None)

    login_data = {"ReturnUrl": return_url, "Username": user_name, "Token": OAUTH_TOKEN}
    session = requests.Session()

    try:
        r = session.post(urljoin(OAUTH_ENDPOINT, "/account/login"), data=login_data, verify=False)
    except (requests.exceptions.ConnectionError, ConnectionRefusedError, http.client.RemoteDisconnected) as e:
        return (DOWN, "Connection error", "Connection error during login: %s" % e, None)
    except requests.exceptions.Timeout as e:
        return (DOWN, "Timeout", "Timeout during login: %s" % e, None)

    return (OK, "", "", session)

def add_link(host, link, session):
    p0ck37_url = f"http://{host}:{PORT}/"
    try:
        r = session.get(urljoin(p0ck37_url, "/add"), params={"link": link}, timeout=TIMEOUT)
    except (requests.exceptions.ConnectionError, ConnectionRefusedError, http.client.RemoteDisconnected) as e:
        return (DOWN, "Connection error", "Connection error during link publishing: %s" % e)
    except requests.exceptions.Timeout as e:
        return (DOWN, "Timeout", "Timeout during link publishing: %s" % e)

    if r.status_code != 200:
        return (MUMBLE, "Can't add new link", "Can't add new link: '%s'" % r.text)

    return (OK, "", "")

def register_flag(flag):
    headers = {"x-api-key": FLAGS_API_KEY}
    data = {"flag": flag}

    try:
        r = requests.post(urljoin(FLAGS_ENDPOINT, "/urls"), headers=headers, json=data)
    except (requests.exceptions.ConnectionError, ConnectionRefusedError, http.client.RemoteDisconnected) as e:
        return (DOWN, "Connection error", "Connection error during link publishing: %s" % e, None)
    except requests.exceptions.Timeout as e:
        return (DOWN, "Timeout", "Timeout during link publishing: %s" % e, None)

    if r.status_code != 200:
        return (CHECKER_ERROR, "Checker error", "Error during flag publishing: %s" % r.text, None)

    if "id" not in r.json():
        return (CHECKER_ERROR, "Checker error", "Can't find 'id' in response: '%s'" % r.text, None)

    return (OK, "", "", r.json()['id'])

def put(args):
    if len(args) != 4:
        verdict(CHECKER_ERROR, "Checker error", "Wrong args count for put()")
    host, flag_id, flag_data, vuln = args
    trace("put(%s, %s, %s, %s)" % (host, flag_id, flag_data, vuln))

    for _ in range(RETRY):
        (status, out, err, secret_flag_id) = register_flag(flag_data)
        if status != OK:
            trace(err)
            continue

        secret_flag_url = urljoin(FLAGS_ENDPOINT, f"/{secret_flag_id}")

        user_name = str(uuid.uuid4())

        (status, out, err, session) = login(host, user_name)
        if status != OK:
            trace(err)
            continue

        (status, out, err) = add_link(host, secret_flag_url, session)
        if status != OK:
            trace(err)
            continue

        (status, out, err) = check_home_page(host, session, secret_flag_id)
        if status != OK:
            trace(err)
            continue

        (status, out, err) = check_pdf(host, session, secret_flag_id, flag_data)
        if status != OK:
            trace(err)
            continue

        break

    if status != OK:
        verdict(status, out, err)

    p0ck37_user_id = hashlib.md5(f"{user_name}{OAUTH_TOKEN}".encode()).hexdigest()
    flag_id = json.dumps({"public_flag_id": p0ck37_user_id, "user_name": user_name, "secret_flag_id": secret_flag_id})
    verdict(OK, flag_id)

def check_home_page(host, session, secret_flag_id):
    p0ck37_url = f"http://{host}:{PORT}/"
    p0ck37_download_url_path = f"/download/{secret_flag_id}.pdf"

    try:
        r = session.get(p0ck37_url, timeout=TIMEOUT)
    except (requests.exceptions.ConnectionError, ConnectionRefusedError, http.client.RemoteDisconnected) as e:
        return (DOWN, "Connection error", "Connection error during getting /: %s" % e)
    except requests.exceptions.Timeout as e:
        return (DOWN, "Timeout", "Timeout during getting /: %s" % e)

    if r.status_code != 200:
        return (MUMBLE, "Can't get /", "Can't get /: '%s'" % r.text)

    if not p0ck37_download_url_path in str(r.content):
        return (CORRUPT, "Can't find flag", "Can't find '%s' in '%s'" % (p0ck37_download_url_path, str(r.content)))

    return (OK, "", "")

def check_pdf(host, session, secret_flag_id, flag):
    p0ck37_url = f"http://{host}:{PORT}/"
    p0ck37_download_url_path = f"/download/{secret_flag_id}.pdf"
    p0ck37_download_url = urljoin(p0ck37_url, p0ck37_download_url_path)

    try:
        r = session.get(p0ck37_download_url, timeout=TIMEOUT)
    except (requests.exceptions.ConnectionError, ConnectionRefusedError, http.client.RemoteDisconnected) as e:
        return (DOWN, "Connection error", "Connection error during link download: %s" % e)
    except requests.exceptions.Timeout as e:
        return (DOWN, "Timeout", "Timeout during link download: %s" % e)

    if r.status_code != 200:
        return (CORRUPT, "Can't download file", "Can't download file: '%s'" % r.text)

    try:
        with pdfplumber.open(io.BytesIO(r.content)) as pdf:
            page = pdf.pages[0]
            text = page.extract_text()
            if flag not in text:
                return (CORRUPT, "Can't find flag in pdf", "Can't find flag in pdf: '%s'" % text)
    except Exception as e:
        return (CORRUPT, "Can't find flag in pdf", "Exception during pdf parsing: %s" % str(e))

    return (OK, "", "")


def get(args):
    if len(args) != 4:
        verdict(CHECKER_ERROR, "Checker error", "Wrong args count for get()")
    host, flag_id, flag_data, vuln = args
    trace("get(%s, %s, %s, %s)" % (host, flag_id, flag_data, vuln))

    info = json.loads(flag_id)

    (status, out, err, session) = login(host, info["user_name"])
    if status != OK:
        verdict(status, out, err)

    p0ck37_url = f"http://{host}:{PORT}/"
    p0ck37_download_url_path = f"/download/{info['secret_flag_id']}.pdf"
    p0ck37_download_url = urljoin(p0ck37_url, p0ck37_download_url_path)

    (status, out, err) = check_home_page(host, session, info['secret_flag_id'])
    if status != OK:
        verdict(status, out, err)

    (status, out, err) = check_pdf(host, session, info['secret_flag_id'], flag_data)
    if status != OK:
        verdict(status, out, err)

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
