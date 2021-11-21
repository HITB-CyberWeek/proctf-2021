#!/usr/bin/env python3
import argparse
import asyncio
import os
import re
import time
import typing

import sanic
from sanic import Sanic
from sanic.log import logger
from sanic.response import json, text, html

DEFAULT_PORT = 9000
FIRMWARE = "firmware.bin"
AUTH_COOKIE = "auth"
READ_BUF_SIZE = 256

app = Sanic("HSM webapp")
fw_lock = None  # type: typing.Optional[asyncio.Lock]
fw_queries = None  # type: typing.Optional[asyncio.Queue]
fw_proc = None  # type: typing.Optional[asyncio.subprocess.Process]
prompt_re = re.compile(r"\[HSM/.*")
hex_re = re.compile("[0-9a-fA-F]+")


class FwQuery:
    def __init__(self, command: str):
        self.command = command
        self.response = None
        self.completed = asyncio.Event()

    def finish(self, response):
        self.response = response
        self.completed.set()


def link(url: str, txt: str = None):
    return "<a href='{}'>{}</a>".format(url, txt or url)


def html_form(action: str, name: str, maxlength: int, width_px: int):
    return "<form method='POST' action='{a}'>"\
           "<input name='{n}' maxlength='{m}' style='width: {w}px;'><input type='submit'>"\
           "</form>".format(a=action, n=name, m=maxlength, w=width_px)


def authenticate():
    return 0  # FIXME


# Note: must be called under fw_lock!
async def fw_write_unsafe(proc: asyncio.subprocess.Process, data: str):
    logger.info("Sending command to firmware: %r ...", data)
    proc.stdin.write((data + "\n").encode())
    await proc.stdin.drain()


# Note: must be called under fw_lock!
async def fw_read_unsafe(proc: asyncio.subprocess.Process, timeout=3):
    data = b""
    start = time.monotonic()
    while time.monotonic() < start + timeout:
        try:
            part = await asyncio.wait_for(proc.stdout.read(READ_BUF_SIZE), 0.005)
            data += part
        except asyncio.exceptions.TimeoutError:
            pass
        if data.endswith(b"]> "):
            response = data.decode(errors="replace")
            response = re.sub(prompt_re, "", response).strip()
            logger.info("Firmware response: %r.", response)
            return response
    logger.warning("Firmware read has timed out after %.2f sec.", timeout)
    return ""


async def fw_communicate(command: str):
    try:
        query = FwQuery(command)
        await fw_queries.put(query)
        logger.info("Waiting for query to complete ...")
        await query.completed.wait()  # FIXME: if qemu terminated unexpectedly and restarted, hangs here.
        logger.info("The query has completed")
        return query.response
    except Exception:
        logger.exception("Firmware communication problem.")
        return "Error: firmware communication problem."


# @app.exception(Exception)
# async def catch_error(request: sanic.Request, exception: Exception):
#     logger.warning("Unhandled exception: %s.", exception)
#     return text("Internal error.", status=500)


@app.route("/")
async def root(request: sanic.Request):
    cookie = request.cookies.get(AUTH_COOKIE)
    if cookie:
        actions = ["generate", "setmeta", "getmeta", "decrypt", "getplaintext", "logout"]
    else:
        actions = ["register", "login"]
    return html("Welcome to the Cloud HSM Service. " + ", ".join([link(a) for a in actions]))


@app.route("/generate")
async def generate(request: sanic.Request):
    response = await fw_communicate("GENERATE")
    slot = 0  # FIXME
    return text("{}:{}".format(response, slot))


@app.route("/getplaintext")
async def getplaintext(request: sanic.Request):
    slot = 0  # FIXME
    response = await fw_communicate("GETPLAINTEXT {}".format(slot))
    return text(response)


@app.route("/getmeta")
async def getmeta(request: sanic.Request):
    slot = 0  # FIXME
    response = await fw_communicate("GETMETA {}".format(slot))
    return text(response)


@app.route("/setmeta", methods=["GET"])
async def setmeta_get(request: sanic.Request):
    return html(html_form(action="setmeta", name="value", maxlength=33, width_px=400))


@app.route("/setmeta", methods=["POST"])
async def setmeta_post(request: sanic.Request):
    slot = authenticate()
    if slot is None:
        return text("Forbidden.", 403)
    value = request.form.get("value")
    if value is None:
        return text("No value.", 400)
    if not value.isalnum():
        return text("Invalid charset.", 400)
    if len(value) > 33:
        return text("Too long.", 400)
    response = await fw_communicate("SETMETA {} {}".format(slot, value))
    return text(response)


@app.route("/decrypt", methods=["GET"])
async def decrypt_get(request: sanic.Request):
    return html(html_form(action="decrypt", name="value", maxlength=200, width_px=800))


@app.route("/decrypt", methods=["POST"])
async def decrypt_post(request: sanic.Request):
    slot = authenticate()
    if slot is None:
        return text("Forbidden.", 403)
    value = request.form.get("value")
    if value is None:
        return text("No value.", 400)
    if len(value) > 200:
        return text("Too long.", 400)
    if not value.isalnum():
        return text("Invalid charset.", 400)
    response = await fw_communicate("DECRYPT {} {}".format(slot, value))
    return text(response)


@app.route("/login")
async def login(request: sanic.Request):
    response = html("Login succeeded. " + link("/", txt="back"))
    response.cookies[AUTH_COOKIE] = "FIXME"
    response.cookies[AUTH_COOKIE]["max-age"] = 3600
    return response


@app.route("/logout")
async def logout(request: sanic.Request):
    response = html("Logout succeeded. " + link("/", txt="back"))
    del response.cookies[AUTH_COOKIE]
    return response


@app.route("/favicon.ico")
async def favicon(request: sanic.Request):
    return text("")


@app.listener("after_server_start")
async def after_server_start(s: Sanic, loop: asyncio.AbstractEventLoop) -> None:
    global fw_queries
    global fw_lock
    fw_lock = asyncio.Lock()
    fw_queries = asyncio.Queue()
    s.add_task(firmware_start_task())
    s.add_task(firmware_communicate_task())
    s.add_task(firmware_stderr_reading_task())


async def firmware_start_task():
    global fw_proc
    while True:
        proc = await run_firmware()
        async with fw_lock:
            await fw_read_unsafe(proc, timeout=5)
        fw_proc = proc
        while fw_proc.returncode is None:
            await asyncio.sleep(0.5)
        proc = fw_proc
        fw_proc = None
        logger.error("Firmware has unexpectedly terminated with exit code %d.", proc.returncode)
        stdout, stderr = await proc.communicate()
        logger.warning("Stdout: %r", stdout.decode(errors="replace"))
        logger.warning("Stderr: %r", stderr.decode(errors="replace"))
        await asyncio.sleep(1)


async def firmware_communicate_task():
    while True:
        query = await fw_queries.get()  # type: FwQuery
        logger.info("Got new query from queue.")
        try:
            async with fw_lock:
                logger.info("Lock acquired.")
                if fw_proc is None:
                    logger.warning("Firmware is not running.")
                    query.finish("Firmware is not running. Try again later.")
                    break
                await fw_write_unsafe(fw_proc, query.command)
                logger.info("Waiting for response from firmware...")
                response = await fw_read_unsafe(fw_proc)
                query.finish(response)
                logger.info("Releasing lock...")
            logger.info("Lock released.")
        except Exception:
            logger.exception("Firmware communication problem.")
            query.finish("Firmware communication problem. Try again later.")


async def firmware_stderr_reading_task():
    while True:
        await asyncio.sleep(1)
        try:
            if fw_proc is None:
                continue
            err_line = await fw_proc.stderr.readline()
            err_line = err_line.strip()
            logger.warning("Firmware stderr: %r.", err_line)
        except Exception as e:
            logger.warning("Stderr reading problem: %s.", e)


async def run_firmware():
    env = os.environ.copy()
    env["QEMU_AUDIO_DRV"] = "none"
    args = ["qemu-system-lm32", "-M", "milkymist", "-kernel", FIRMWARE, "-nographic"]
    # args = ["./proxy.sh"] + args
    # proc = await asyncio.create_subprocess_shell(" ".join(args),
    #                                              env=env,
    #                                              stdin=asyncio.subprocess.PIPE,
    #                                              stdout=asyncio.subprocess.PIPE,
    #                                              stderr=asyncio.subprocess.PIPE)
    proc = await asyncio.create_subprocess_exec(*args,
                                                env=env,
                                                limit=64*1024,
                                                stdin=asyncio.subprocess.PIPE,
                                                stdout=asyncio.subprocess.PIPE,
                                                stderr=asyncio.subprocess.PIPE)
    logger.info("Started firmware [%d]", proc.pid)
    return proc


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9000)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    app.run(host=args.host, port=args.port)
