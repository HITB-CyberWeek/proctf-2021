#!/usr/bin/env python3
import argparse
import asyncio
import base64
import os
import random
import re
import string
import time
import typing

import sanic
from aiofile import async_open
from sanic import Sanic
from sanic.log import logger
from sanic.response import text, html, redirect
import sanic.exceptions

from Crypto.PublicKey import RSA

from slot import LastSlotStorage
from users import UsersDB, UserAlreadyExists, AuthenticationError, USER_TTL_SECONDS, User

DEFAULT_PORT = 9000
FIRMWARE = "firmware.exe"
AUTH_COOKIE = "auth"
USERS_DB_DIR = "state/users"
READ_BUF_SIZE = 256
SLOT_AREA_START = 0x4002f530  # Keep in sync with firmware!
SLOT_AREA_SIZE = 392*25*30    # Keep in sync with firmware!
SLOT_AREA_FILE = "state/slots.dump"
TOKEN_TTL = 120


app = Sanic("HSM Web Application")

fw_lock = None  # type: typing.Optional[asyncio.Lock]
fw_query_queue = None  # type: typing.Optional[asyncio.Queue]
fw_stdin_queue = None  # type: typing.Optional[asyncio.Queue]
fw_stdout_queue = None  # type: typing.Optional[asyncio.Queue]
fw_stderr_queue = None  # type: typing.Optional[asyncio.Queue]
fw_proc = None  # type: typing.Optional[asyncio.subprocess.Process]
users_db = None  # type: typing.Optional[UsersDB]
cookies = dict()  # str -> users.User
last_slot_storage = None  # type: typing.Optional[LastSlotStorage]

prompt_re = re.compile(r"\[HSM/.*")
hex_re = re.compile("[0-9a-fA-F]+")

n = 115045776722470139950834985511737824169203361636247716192455037317286230881780626315900908860725963302859444324037742351913758930132166050849355540323239340689604235624481276703667146476431189318574778905263482734541820821322526067825430087789925145767614519151104945454389067905075159840131241166366538396261
e = 65537
pubkey = RSA.construct((n, e),)
used_tokens = set()


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


def html_form(action: str, width_px: int, inputs: list, comment: str = None):
    result = "<form method='POST' action='{}'>\n".format(action)
    for name, maxlength in inputs:
        result += "<label for='{n}'>{n}</label><br/>".format(n=name)
        result += "<input name='{n}' maxlength='{m}' style='width: {w}px;'/><br/>\n".format(
            n=name, m=maxlength, w=width_px)
    if comment is not None:
        result += comment + "<br/>"
    result += "<br/><input type='submit' value='Submit'/>\n"
    result += "</form>"
    return result


def validated(form: sanic.request.RequestParameters, name: str, maxlen: int, allow_non_alnum: bool = False):
    value = form.get(name)
    if not value:
        raise sanic.exceptions.InvalidUsage("No value for required parameter: {!r}.".format(name))
    if len(value) > maxlen:
        raise sanic.exceptions.PayloadTooLarge("Too big value: {!r} ({}).".format(name,  len(value)))
    if not allow_non_alnum and not value.isalnum():
        raise sanic.exceptions.InvalidUsage("Value is not alphanumeric: {!r} [{}].".format(name, value))
    return value


def get_user_from_cookie(request: sanic.Request) -> User:
    cookie_value = request.cookies.get(AUTH_COOKIE)
    user = cookies.get(cookie_value)
    logger.info("Cookie: %r, user: %r.", cookie_value, user.username if user is not None else None)
    return user


def random_string(length):
    return "".join(random.choice(string.ascii_lowercase) for i in range(length))


async def fw_write_unsafe(proc: asyncio.subprocess.Process, data: str):
    logger.info("[ in] Write to stdin: %r ...", data)
    data = data + "\n"
    chunk_size = 32
    # Note: there is a 128-byte serial port buffer in firmware, avoid its overloading.
    # FIXME: read after each write!
    for chunk in [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]:
        proc.stdin.write(chunk.encode())
        await proc.stdin.drain()
        await asyncio.sleep(0.01)


async def fw_read_unsafe(proc: asyncio.subprocess.Process):
    data = await proc.stdout.readline()
    if len(data) == 0:
        raise EOFError()  # Probably the process is terminating.
    line = data.decode(errors="replace").strip()
    logger.info("[out] Got: %r.", line)
    return line


async def fw_communicate(command: str):
    try:
        query = FwQuery(command)
        await fw_query_queue.put(query)
        logger.info("Put query %r to the queue, waiting for completion...", command)
        await query.completed.wait()  # FIXME: if qemu terminated unexpectedly and restarted, hangs here.
        logger.info("Query %r has completed.", command)
        return query.response
    except Exception:
        logger.exception("Firmware communication problem.")
        return "Error: firmware communication problem."


@app.route("/")
async def root(request: sanic.Request):
    user = get_user_from_cookie(request)
    if user and not user.is_expired():
        message = "Welcome to the Cloud HSM Service [{} / {}]. ".format(user.username, user.slot)
        if user.slot is None:
            actions = ["generate", "logout"]
        else:
            actions = ["setmeta", "getmeta", "decrypt", "getplaintext", "logout"]
    else:
        message = "To use Cloud HSM Service, you must: "
        actions = ["register", "login"]
    return html(message + ", ".join([link(a) for a in actions]))


@app.route("/register", methods=["GET"])
async def register_get(request: sanic.Request):
    return html(html_form(action="register", width_px=300, inputs=[
        ("username", 32),
        ("password", 32),
        ("hsm_token", 240),
    ], comment="<i>issue new hsm-token at " + link("https://hsm-auth.ctf.hitb.org/") + "</i>"))


def unpack_bigint(b: bytes) -> int:
    return sum((1 << (bi*8)) * bb for (bi, bb) in enumerate(b))


def validate_hsm_token(t: str):
    a = t.split("_")
    if len(a) != 4:
        return text("Incorrect token format", 400)
    type_, data, ts, signature = a

    if type_ != "HSM":
        return text("Wrong token type: HSM_{...} required.", 400)

    ts = int(ts)
    if ts - time.time() > TOKEN_TTL:
        return text("Token is from future ({:.2f} sec)".format(ts - time.time()), 400)
    if time.time() - ts > TOKEN_TTL:
        return text("Token has expired", 400)
    try:
        signature_bytes = base64.b64decode(signature)
        signature_rsa = (unpack_bigint(signature_bytes),)
    except:
        return text("Incorrect signature format", 400)
    signed_data = "{}_{}".format(data, ts).encode()
    if not pubkey.verify(signed_data, signature_rsa):
        return text("Signature verification failed", 400)

    return None


@app.route("/register", methods=["POST"])
async def register_post(request: sanic.Request):
    username = validated(request.form, "username", maxlen=32)
    password = validated(request.form, "password", maxlen=32)
    token = validated(request.form, "hsm_token", maxlen=240, allow_non_alnum=True)

    if token in used_tokens:
        return text("I've seen this token already, sorry. You need another one.", 400)

    err = validate_hsm_token(token)
    if err is not None:
        return err
    used_tokens.add(token)

    try:
        user = await users_db.add(username, password)
    except ValueError:
        return text("Validation has failed", 400)
    except UserAlreadyExists:
        return text("User already exists", 403)

    cookie = random_string(64)
    cookies[cookie] = user
    logger.info("Register succeeded, set cookie '%s...' for user %r.", cookie[:16], user.username)
    response = redirect("/")
    response.cookies[AUTH_COOKIE] = cookie
    response.cookies[AUTH_COOKIE]["max-age"] = USER_TTL_SECONDS
    return response


@app.route("/generate")
async def generate(request: sanic.Request):
    user = get_user_from_cookie(request)
    if not user or user.is_expired():
        return redirect("/")
    if user.slot is not None:
        return text("Already generated keypair", 403)
    async with last_slot_storage.lock:
        response = await fw_communicate("GENERATE")
        slot, pubkey = response.split(" = ")
        await last_slot_storage.write(int(slot))
    user.slot = slot
    await users_db.update(user)
    return text("{}".format(response))


@app.route("/getplaintext")
async def getplaintext(request: sanic.Request):
    user = get_user_from_cookie(request)
    if not user or user.is_expired():
        return redirect("/")
    response = await fw_communicate("GETPLAINTEXT {}".format(user.slot))
    return text(response)


@app.route("/getmeta")
async def getmeta(request: sanic.Request):
    user = get_user_from_cookie(request)
    if not user or user.is_expired():
        return redirect("/")
    response = await fw_communicate("GETMETA {}".format(user.slot))
    return text(response)


@app.route("/setmeta", methods=["GET"])
async def setmeta_get(request: sanic.Request):
    user = get_user_from_cookie(request)
    if not user or user.is_expired():
        return redirect("/")
    return html(html_form(action="setmeta", width_px=400, inputs=[("meta", 33)]))


@app.route("/setmeta", methods=["POST"])
async def setmeta_post(request: sanic.Request):
    user = get_user_from_cookie(request)
    if not user or user.is_expired():
        return redirect("/")
    meta = validated(request.form, "meta", maxlen=33)
    response = await fw_communicate("SETMETA {} {}".format(user.slot, meta))
    return text(response)


@app.route("/decrypt", methods=["GET"])
async def decrypt_get(request: sanic.Request):
    user = get_user_from_cookie(request)
    if not user or user.is_expired():
        return redirect("/")
    return html(html_form(action="decrypt", width_px=800, inputs=[("ciphertext", 260)]))


@app.route("/decrypt", methods=["POST"])
async def decrypt_post(request: sanic.Request):
    user = get_user_from_cookie(request)
    if not user or user.is_expired():
        return redirect("/")
    if user.op_counter <= 0:
        return text("Your decrypt limit has exceeded")
    user.op_counter -= 1
    await users_db.update(user)
    ciphertext = validated(request.form, "ciphertext", maxlen=260)
    response = await fw_communicate("DECRYPT {} {}".format(user.slot, ciphertext))
    return text(response)


@app.route("/login", methods=["GET"])
async def login_get(request: sanic.Request):
    return html(html_form(action="login", width_px=300, inputs=[
        ("username", 32),
        ("password", 32),
    ]))


@app.route("/login", methods=["POST"])
async def login_post(request: sanic.Request):
    username = validated(request.form, "username", maxlen=32)
    password = validated(request.form, "password", maxlen=32)
    try:
        user = users_db.authenticate(username, password)
    except AuthenticationError as e:
        return text(str(e), 403)

    cookie = random_string(64)
    cookies[cookie] = user
    logger.info("Login succeeded, set cookie '%s...' for user %r.", cookie[:16], user.username)
    response = redirect("/")
    response.cookies[AUTH_COOKIE] = cookie
    response.cookies[AUTH_COOKIE]["max-age"] = USER_TTL_SECONDS
    return response


@app.route("/logout")
async def logout(request: sanic.Request):
    response = redirect("/")
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

    global users_db
    logger.info("Loading users from the database...")
    users_db = UsersDB(USERS_DB_DIR)
    await users_db.load()
    logger.info("Loaded %d user(s).", users_db.count())

    global last_slot_storage
    last_slot_storage = LastSlotStorage()

    logger.info("Staring background tasks...")
    s.background_tasks = [
        loop.create_task(firmware_respawn_task()),
        loop.create_task(firmware_communicate_task()),
        loop.create_task(firmware_stdin_task()),
        loop.create_task(firmware_stdout_task()),
        loop.create_task(firmware_stderr_task()),
        loop.create_task(firmware_state_dump_restore_task()),
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
        await fw_communicate("RANDINIT {}".format(random_string(10)))
        free_slot = await last_slot_storage.read()
        if free_slot >= 0:
            await fw_communicate("SETSLOT {}".format(free_slot))

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
            logger.exception("[ in] Stdin reading error.")
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
            logger.exception("[out] Stdout reading error.")
            await asyncio.sleep(0.1)


async def firmware_stderr_task():
    while True:
        await asyncio.sleep(0.1)
        try:
            if fw_proc is None:
                continue
            err_line = await fw_proc.stderr.readline()
            err_line = err_line.decode(errors="replace").strip()
            logger.warning("[err] Got: %r.", err_line)
        except Exception as e:
            logger.warning("[err] Stderr reading problem: %s.", e)


async def firmware_communicate_task():
    while True:
        query = await fw_query_queue.get()  # type: FwQuery
        logger.info("[com] Got new query from queue.")
        try:
            async with fw_lock:
                logger.info("[com] Lock acquired.")
                await fw_stdin_queue.put(query.command)
                logger.info("[com] Waiting for response from firmware...")
                response = await fw_stdout_queue.get()
                if response != query.command:
                    logger.warning("[com] Unexpected firmware behavior, doesn't echo commands (got %r).", response)
                response = await fw_stdout_queue.get()
                while True:
                    try:
                        # In case of multiline output.
                        response += await asyncio.wait_for(fw_stdout_queue.get(), 0.002)
                    except asyncio.TimeoutError:
                        break
                query.finish(response)
                logger.info("[com] Releasing lock...")
            logger.info("[com] Lock released.")
        except Exception:
            logger.exception("[com] Firmware communication problem.")
            query.finish("[com] Firmware communication problem. Try again later.")


async def firmware_state_dump_restore_task():
    logger.info("[sta] Starting dump restore...")
    buf_size = 100
    try:
        offset = 0
        async with async_open(SLOT_AREA_FILE, "rb") as f:
            while offset < SLOT_AREA_SIZE:
                data = await f.read(buf_size)
                if data != b"\0" * buf_size:
                    response = await fw_communicate("RESTORE {} {}".format(offset, data.hex().upper()))
                    if response != "OK":
                        logger.warning("[sta] Dump restore: unexpected response: %r, aborting.", response)
                        break
                offset += len(data)
        logger.info("[sta] Dump restore completed.")
    except Exception as e:
        logger.warning("[sta] Dump restore problem: %s.", e)

    while True:
        await asyncio.sleep(1)
        try:
            reader, writer = await asyncio.open_unix_connection("qemu-monitor-socket", limit=1024)
            logger.info("[sta] Connected to qemu monitor socket.")
            while True:
                cmd = "memsave 0x{:08x} {} {}\n".format(SLOT_AREA_START, SLOT_AREA_SIZE, SLOT_AREA_FILE)
                writer.write(cmd.encode())
                await writer.drain()
                try:
                    await asyncio.wait_for(reader.read(1024), 0.1)
                except asyncio.TimeoutError:
                    pass
                await asyncio.sleep(1)
        except Exception as e:
            logger.warning("[sta] Firmware dump state problem: %s.", e)


async def run_firmware():
    env = os.environ.copy()
    env["QEMU_AUDIO_DRV"] = "none"
    args = ["qemu-system-lm32", "-M", "milkymist", "-kernel", FIRMWARE, "-nographic",
            "-monitor", "unix:qemu-monitor-socket,server,nowait"]
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
