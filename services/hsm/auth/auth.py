import argparse
import asyncio
import base64
import random
import string
import time
import typing

import sanic
import sanic.exceptions
from sanic.log import logger
from sanic import Sanic, html, text
from Crypto.PublicKey import RSA

app = Sanic("HSM Auth Application")

TOKENS_FILE = "tokens.txt"
TOKEN_TTL = 60
CHECKER_TOKEN = "***REMOVED***"

n = 115045776722470139950834985511737824169203361636247716192455037317286230881780626315900908860725963302859444324037742351913758930132166050849355540323239340689604235624481276703667146476431189318574778905263482734541820821322526067825430087789925145767614519151104945454389067905075159840131241166366538396261
e = 65537
d = 30344405395801132782857524139888918146830787329968994950986126540223229427994261356129562088080153221130481324828973164703621417920634486701892974503372367852896219496589538500675643701904083515839188194935035545233260145550208385262642874377135643731253647349474947472447650795723733262392892760882278131649
p = 10258574343731792996939305140192271788306271223912210245398480052993671598234571686015670964443887353624940201679830989289876177847086535662481003720426893
q = 11214596967147345887960660764742351699902876684882474883493185904692227810458212796134015620502689287257375166852774747591855152877556474034495270149803577
u = 2569967291838043633507624184850081480972182405195472547511394337325274231369479990295446703577155625627081348444887257748019600750299903561838167267264346
privkey = RSA.construct((n, e, d, p, q, u),)
pubkey = RSA.construct((n, e),)

lock = None  # type: typing.Optional[asyncio.Lock]
tokens = dict()  # type: typing.Dict[str, float]


@app.listener("after_server_start")
async def after_server_start(s: Sanic, loop: asyncio.AbstractEventLoop) -> None:
    global lock
    lock = asyncio.Lock()


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


def validated(form: sanic.request.RequestParameters, name: str, maxlen: int):
    value = form.get(name)
    if not value:
        raise sanic.exceptions.InvalidUsage("No value for required parameter: {!r}.".format(name))
    if len(value) > maxlen:
        raise sanic.exceptions.PayloadTooLarge("Too big value: {!r} ({}).".format(name,  len(value)))
    return value


def pack_bigint(i: int) -> bytes:
    b = bytearray()
    while i:
        b.append(i & 0xFF)
        i >>= 8
    return b


def create_hsm_token():
    data = "".join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=16))
    data += "_{}".format(int(time.time()))
    data_bytes = data.encode()
    logger.info("Creating signature for data %r", data)
    signature = privkey.sign(data_bytes, "")[0]
    logger.info("Signature (int) is %d", signature)
    signature_b64 = base64.b64encode(pack_bigint(signature)).decode()
    return "HSM_{}_{}".format(data, signature_b64)


@app.route("/", methods=["GET"])
async def root(request: sanic.Request):
    return html(html_form(action="", width_px=400, inputs=[
        ("oauth_token", 41)
    ], comment="^ paste you OAUTH_{{...}} token here to get one-time HSM_{{...}} token. <br/>"
               "You are allowed to issue one hsm-token per {} seconds.".format(TOKEN_TTL)))


@app.route("/", methods=["POST"])
async def root(request: sanic.Request):
    global lock
    global privkey
    oauth_token = validated(request.form, "oauth_token", 41)
    if oauth_token == CHECKER_TOKEN:
        return text(create_hsm_token())

    async with lock:
        ts = tokens.get(oauth_token)
        if ts is None:
            logger.warning("Denied: unknown token: %s...", oauth_token[:16])
            raise sanic.exceptions.NotFound("Unknown token.")
        age = time.monotonic() - ts
        if age < TOKEN_TTL:
            logger.warning("Denied: too fast: %s...", oauth_token[:16])
            raise sanic.exceptions.Forbidden("Please wait {:.1f} sec.".format(TOKEN_TTL - age))
        tokens[oauth_token] = time.monotonic()
    logger.info("Creating token for oauth token %s...", oauth_token[:16])
    return text(create_hsm_token())


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9001)
    return parser.parse_args()


def load_tokens():
    global tokens
    with open(TOKENS_FILE) as f:
        for line in f.readlines():
            tokens[line.strip()] = 0


if __name__ == "__main__":
    args = parse_args()
    load_tokens()
    app.run(host=args.host, port=args.port)
