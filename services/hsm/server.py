#!/usr/bin/env python3
import argparse
import asyncio
import os
import random
import re
import string
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
fw_query_queue = None  # type: typing.Optional[asyncio.Queue]
fw_stdin_queue = None  # type: typing.Optional[asyncio.Queue]
fw_stdout_queue = None  # type: typing.Optional[asyncio.Queue]
fw_stderr_queue = None  # type: typing.Optional[asyncio.Queue]

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


class StdoutStuckException(Exception):
    pass


def link(url: str, txt: str = None):
    return "<a href='{}'>{}</a>".format(url, txt or url)


def html_form(action: str, name: str, maxlength: int, width_px: int):
    return "<form method='POST' action='{a}'>"\
           "<input name='{n}' maxlength='{m}' style='width: {w}px;'><input type='submit'>"\
           "</form>".format(a=action, n=name, m=maxlength, w=width_px)


def authenticate():
    return 0  # FIXME


def random_string(length):
    return "".join(random.choice(string.ascii_lowercase) for i in range(length))


async def fw_write_unsafe(proc: asyncio.subprocess.Process, data: str):
    logger.info("Sending command to firmware: %r ...", data)
    data = data + "\n"
    chunk_size = 32
    # Note: there is a 128-byte serial port buffer in firmware, avoid its overloading.
    for chunk in [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]:
        proc.stdin.write(chunk.encode())
        await proc.stdin.drain()
        await asyncio.sleep(0.01)


async def fw_read_unsafe(proc: asyncio.subprocess.Process):
    data = await proc.stdout.readline()
    if len(data) == 0:
        raise EOFError()  # Probably the process is terminating.
    line = data.decode(errors="replace").strip()
    logger.info("Firmware stdout: %r.", line)
    return line


async def fw_communicate(command: str):
    try:
        query = FwQuery(command)
        await fw_query_queue.put(query)
        logger.info("Waiting for query to complete ...")
        await query.completed.wait()  # FIXME: if qemu terminated unexpectedly and restarted, hangs here.
        logger.info("The query has completed")
        return query.response
    except Exception:
        logger.exception("Firmware communication problem.")
        return "Error: firmware communication problem."


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
    global fw_query_queue
    fw_query_queue = asyncio.Queue()
    global fw_lock
    fw_lock = asyncio.Lock()
    global fw_stdin_queue
    fw_stdin_queue = asyncio.Queue()
    global fw_stdout_queue
    fw_stdout_queue = asyncio.Queue()
    global fw_stderr_queue
    fw_stderr_queue = asyncio.Queue()

    logger.info("Staring background tasks.")
    s.background_tasks = [
        loop.create_task(firmware_respawn_task()),
        loop.create_task(firmware_communicate_task()),
        loop.create_task(firmware_stdin_task()),
        loop.create_task(firmware_stdout_task()),
        loop.create_task(firmware_stderr_task()),
    ]


@app.listener("before_server_stop")
async def before_server_stop(s: Sanic, loop: asyncio.AbstractEventLoop) -> None:
    logger.info("Stopping background tasks.")
    for task in s.background_tasks:
        task.cancel()
        await task


async def firmware_respawn_task():
    global fw_proc
    while True:
        proc = await run_firmware()
        fw_proc = proc
        await fw_communicate("RANDINIT " + random_string(10))
        while fw_proc.returncode is None:
            await asyncio.sleep(0.1)
        proc = fw_proc
        fw_proc = None
        logger.error("Firmware has unexpectedly terminated with exit code %d.", proc.returncode)
        stdout, stderr = await proc.communicate()
        logger.warning("Stdout: %r", stdout.decode(errors="replace"))
        logger.warning("Stderr: %r", stderr.decode(errors="replace"))
        await asyncio.sleep(0.1)


async def firmware_stdin_task():
    while True:
        try:
            line = await fw_stdin_queue.get()
            await fw_write_unsafe(fw_proc, line)
        except AttributeError:  # Qemu is restarting, fw_proc is None.
            await asyncio.sleep(0.1)
            continue
        except Exception:
            logger.exception("Stdin reading error.")
            await asyncio.sleep(0.1)


async def firmware_stdout_task():
    while True:
        try:
            line = await fw_read_unsafe(fw_proc)
            await fw_stdout_queue.put(line)
        except AttributeError:  # Qemu is restarting, fw_proc is None.
            await asyncio.sleep(0.1)
            continue
        except Exception:
            logger.exception("Stdout reading error.")
            await asyncio.sleep(0.1)


async def firmware_stderr_task():
    while True:
        await asyncio.sleep(0.1)
        try:
            if fw_proc is None:
                continue
            err_line = await fw_proc.stderr.readline()
            err_line = err_line.decode(errors="replace").strip()
            logger.warning("Firmware stderr: %r.", err_line)
        except Exception as e:
            logger.warning("Stderr reading error: %s.", e)


async def firmware_communicate_task():
    while True:
        query = await fw_query_queue.get()  # type: FwQuery
        logger.info("Got new query from queue.")
        try:
            async with fw_lock:
                logger.info("Lock acquired.")
                await fw_stdin_queue.put(query.command)
                logger.info("Waiting for response from firmware...")
                response = await fw_stdout_queue.get()
                if response != query.command:
                    logger.warning("Unexpected firmware behavior, doesn't echo commands (got %r).", response)
                response = await fw_stdout_queue.get()
                while True:
                    try:
                        # In case of multiline output.
                        response += await asyncio.wait_for(fw_stdout_queue.get(), 0.002)
                    except asyncio.TimeoutError:
                        break
                query.finish(response)
                logger.info("Releasing lock...")
            logger.info("Lock released.")
        except Exception:
            logger.exception("Firmware communication problem.")
            query.finish("Firmware communication problem. Try again later.")


async def run_firmware():
    env = os.environ.copy()
    env["QEMU_AUDIO_DRV"] = "none"
    args = ["qemu-system-lm32", "-M", "milkymist", "-kernel", FIRMWARE, "-nographic"]
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
