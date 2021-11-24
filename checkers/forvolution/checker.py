#!/usr/bin/env python3

import time
start = time.time()

import sys
import string
import asyncio
import random
import traceback
import numpy as np
import json
import hashlib
import base64
import re

from asyncio import open_connection, IncompleteReadError, LimitOverrunError
from client import Error
import client

OK, CORRUPT, MUMBLE, DOWN, CHECKER_ERROR = 101, 102, 103, 104, 110

PORT = 12345
MIN_MATRIX_SIZE = 2
MAX_MATRIX_SIZE = 35
MAX_PUT_MATRIX_SIZE_2 = 31
MIN_PUT_MATRIX_SIZE_2 = 17
MAX_KERNEL_SIZE = 10
MIN_TEXT_SIZE = 1
MAX_TEXT_SIZE = 99

ID_FORMAT = re.compile('[0-9a-f]{%d}' % client.ID_BSIZE)

printable = (string.digits + string.ascii_letters).encode()

def verdict(exit_code, public="", private=""):
    if public:
        print(public)
    if private:
        print(private, file=sys.stderr)
    sys.exit(exit_code)

def log(*message):
    print('{: 2.05f}'.format(time.time() - start), *message, file=sys.stderr)
    sys.stderr.flush()

def get_rand_matrix_content(n, m):
    return [[random.randint(-128, 127) for _ in range(m)] for _ in range(n)]

def get_rand_matrix(l, r):
    n, m = (random.randint(l, r) for _ in range(2))
    return get_rand_matrix_content(n, m)

def get_rand_square_matrix(l, r):
    n = random.randint(l, r)
    return get_rand_matrix_content(n, n)

def get_rand_text(l, r):
    if random.randint(0, 50):
        data = [random.choice(printable) for _ in range(random.randint(l, r))]
    else:
        data = [random.randint(0, 255) for _ in range(random.randint(l, r))]
    return bytes(data).decode(encoding='utf-8', errors='surrogateescape')

def get_size(m):
    return (len(m), 0 if len(m) == 0 else len(m[0]))

def get_matrix_hash(m):
    h = hashlib.sha256()
    h.update(json.dumps(m).encode())
    return h.hexdigest()

def compare(m1, m2):
    s1 = get_size(m1)
    s2 = get_size(m2)

    if s1 != s2:
        verdict(MUMBLE, 'matrixes have different size', 'matrixes have different size: checker %s vs service %s' % (str(s1), str(s2)))

    bads = 0
    last = None
    for x in range(s1[0]):
        for y in range(s1[1]):
            if m1[x][y] != m2[x][y]:
                bads += 1
                last = (x, y)

    if bads > 0:
        verdict(MUMBLE, 'matrixes have different elements', 'matrixes have different elements at %d positions. Example: %s checker %d vs service %d' 
                % (bads, str(last), m1[last[0]][last[1]], m2[last[0]][last[1]]))

def calc_convolution(matrix, kernel):
    m = np.array(matrix)
    k = np.array(kernel)

    output = np.zeros((m.shape[0] - k.shape[0] + 1, m.shape[1] - k.shape[1] + 1))

    for x in range(output.shape[0]):
        for y in range(output.shape[1]):
            output[x, y] = (k * m[x:x+k.shape[0], y:y+k.shape[1]]).sum()

    return output.tolist()

async def sleep_rand(name, k):
    t = random.random() * k
    log('[%s] sleep for %.3f' % (name, t))
    await asyncio.sleep(t)

class LoggedClient(client.Client):
    def __init__(self, name, host, port):
        super().__init__(host, port)
        self.connected = False
        self.name = name
    async def connect(self):
        await sleep_rand(self.name, 1)
        log('[%s] try connect to %s:%d' % (self.name, self.host, self.port))
        await super().connect()
        log('[%s] connected' % self.name)
        self.connected = True
    async def upload(self, matrix, desc, key):
        if not self.connected:
            await self.connect()
        await sleep_rand(self.name, 1)
        log('[%s] try upload matrix %dx%d with desc %s and key %s' % (self.name, len(matrix), len(matrix[0]), repr(desc), repr(key)))
        mid = await super().upload(matrix, desc, key)
        log('[%s] uploaded to id %s' % (self.name, repr(mid)))
        return mid
    async def download(self, mid, key):
        if not self.connected:
            await self.connect()
        await sleep_rand(self.name, 1)
        log('[%s] try download matrix with id %s and key %s' % (self.name, repr(mid), repr(key)))
        matrix, desc = await super().download(mid, key)
        size = get_size(matrix)
        log('[%s] downloaded matrix %dx%d with desc %s' % (self.name, size[0], size[1], repr(desc)))
        return matrix, desc
    async def convolution(self, mid, kernel):
        if not self.connected:
            await self.connect()
        await sleep_rand(self.name, 1)
        log('[%s] try calculate convolution for id %s with kernel %dx%d' % (self.name, repr(mid), len(kernel), len(kernel[0])))
        convolution = await super().convolution(mid, kernel)
        size = get_size(convolution)
        log('[%s] convolution calculated: result is %dx%d' % (self.name, size[0], size[1]))
        return convolution

async def info():
    verdict(OK, 'vulns: 1\npublic_flag_description: Flag ID is image ID, flag is description of image')

def generate_data_for_check(seed):
    log('seed:', seed)

    random.seed(a=seed, version=2)

    matrix = get_rand_matrix(MIN_MATRIX_SIZE, MAX_MATRIX_SIZE)
    desc = get_rand_text(MIN_TEXT_SIZE, MAX_TEXT_SIZE)
    key = get_rand_text(MIN_TEXT_SIZE, MAX_TEXT_SIZE)
    kernels = generate_kernels(len(matrix), len(matrix[0]))
    return (matrix, desc, key, kernels)

def check_id(mid):
    if not ID_FORMAT.fullmatch(mid):
        verdict(MUMBLE, 'Incorrect id format', 'Incorrect id format: %s' % repr(mid))

async def check(host):

    seed = ''.join((random.choice(string.ascii_letters)) for _ in range(10))
    matrix, desc, key, kernels = generate_data_for_check(seed)
    mode = random.randint(0, 10)

    client = LoggedClient('default', host, PORT)
    mid = await client.upload(matrix, desc, key)

    check_id(mid)

    dmatrix, ddesc, convolutions = await fire(mode, client, mid, key, kernels)

    if desc != ddesc:
        verdict(MUMBLE, 'Descriptions are different', 'Descriptions are different: checker "%s" vs service "%s"' % (desc, ddesc))
    compare(matrix, dmatrix)

    for i in range(len(kernels)):
        convolution = calc_convolution(matrix, kernels[i])
        compare(convolution, convolutions[i])

    verdict(OK, 'ok')

def generate_data_for_put(seed):
    log('seed:', seed)

    random.seed(a=seed, version=2)

    mode = random.randint(0, 1)
    if mode:
        matrix = get_rand_matrix(MIN_PUT_MATRIX_SIZE_2, MAX_PUT_MATRIX_SIZE_2)
    else:
        matrix = get_rand_matrix(MAX_PUT_MATRIX_SIZE_2 + 1, MAX_MATRIX_SIZE)
    key = get_rand_text(MIN_TEXT_SIZE, MAX_TEXT_SIZE)
    return (matrix, key)

async def put(host, flag_id, flag, vuln):
    matrix, key = generate_data_for_put(flag_id)

    client = LoggedClient('default', host, PORT)
    await client.connect()

    mid = await client.upload(matrix, flag, key)

    check_id(mid)

    n, m = get_size(matrix)
    verdict(OK, json.dumps({
        'public_flag_id': mid,
        'flag_id': flag_id,
        'matrix': {
            'n': n,
            'm': m,
            'hash': get_matrix_hash(matrix)
            },
        'key': base64.b64encode(key.encode(encoding='utf-8', errors='surrogateescape')).decode()
    }))

def generate_kernels(n, m):
    res = []
    for _ in range(max(1, random.randint(0, 15) - 10)):
        res.append(get_rand_square_matrix(MIN_MATRIX_SIZE, min(n, m, MAX_KERNEL_SIZE)))
        log('use kernel %s' % json.dumps(res[-1]))
    return res

async def fire(mode, client, mid, key, kernels):
    if mode:
        perm = list(range(-1, len(kernels)))
        random.shuffle(perm)
        convolutions = [0] * len(kernels)
        for i in perm:
            if i < 0:
                matrix, desc = await client.download(mid, key)
            else:
                convolutions[i] = await client.convolution(mid, kernels[i])
    else:
        tasks = [asyncio.create_task(LoggedClient('download', client.host, client.port).download(mid, key))]
        for i in range(len(kernels)):
            tasks.append(asyncio.create_task(LoggedClient('convolution %d' % i, client.host, client.port).convolution(mid, kernels[i])))

        _ = await asyncio.wait(tasks)

        matrix, desc = await tasks[0]
        convolutions = [await task for task in tasks[1:]]

    return matrix, desc, convolutions


async def get(host, flag_id, flag, vuln):
    d = json.loads(flag_id)
    flag_id = d['flag_id']
    mid = d['public_flag_id']
    matrix = d['matrix']
    key = base64.b64decode(d['key']).decode(encoding='utf-8', errors='surrogateescape')
    mode = random.randint(0, 9)

    kernels = generate_kernels(matrix['n'], matrix['m'])
    client = LoggedClient('default', host, PORT)

    try:
        dmatrix, ddesc, convolutions = await fire(mode, client, mid, key, kernels)
    except Error as e:
        if e.error == 'image is not found':
            verdict(CORRUPT, 'Flag not found', 'Flag not found: %s' % traceback.format_exc())
        else:
            raise

    if flag != ddesc:
        verdict(CORRUPT, 'Flag is broken', 'Flag is broken: checker "%s" vs service "%s"' % (flag, ddesc))
    h = get_matrix_hash(dmatrix)
    if h != matrix['hash']:
        verdict(MUMBLE, 'Matrixes are different', 'Matrixes are different: checker %s vs service %s' % (matrix['hash'], h))
    for i in range(len(kernels)):
        convolution = calc_convolution(dmatrix, kernels[i])
        compare(convolution, convolutions[i])

    verdict(OK, 'ok')


async def print_debug(method, seed):
    if method == 'check':
        data = generate_data_for_check(seed)
    elif method == 'put':
        data = generate_data_for_put(seed)
    print(json.dumps(data))
    verdict(OK)

def main(args):
    CMD_MAPPING = {
        "info": (info, 0),
        "check": (check, 1),
        "put": (put, 4),
        "get": (get, 4),
        "DEBUG": (print_debug, 2)
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
        asyncio.run(handler(*args))

    except Error as E:
        verdict(MUMBLE, "Request error", "Request error: %s" % traceback.format_exc())
    except IncompleteReadError as E:
        verdict(MUMBLE, "Reading error", "Reading error: %s" % traceback.format_exc())
    except LimitOverrunError as E:
        verdict(MUMBLE, "Reading error", "Reading error: %s" % traceback.format_exc())
    except ConnectionRefusedError as E:
        verdict(DOWN, "Connect refused", "Connect refused: %s" % traceback.format_exc())
    except ConnectionError as E:
        verdict(MUMBLE, "Connection aborted", "Connection aborted: %s" % traceback.format_exc())
    except OSError as E:
        verdict(DOWN, "Connect error", "Connect error: %s" % traceback.format_exc())
    except Exception as E:
        verdict(CHECKER_ERROR, "Checker error", "Checker error: %s" % traceback.format_exc())
    verdict(CHECKER_ERROR, "Checker error", "No verdict")

if __name__ == '__main__':
    log('initialized')
    main(sys.argv[1:])
