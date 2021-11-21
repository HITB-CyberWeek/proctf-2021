
from asyncio import open_connection
from enum import Enum, IntEnum

MAX_SIZE = 255
ID_BSIZE = 32

Upload = 'UPLOAD'
Download = 'DOWNLOAD'
Convolution = 'CONVOLUTION'
Delimiter = ';'

class Errors(Enum):
    UnknownCommand = 1
    BadSize = 2
    Unauthorized = 3
    BadFiled = 4
    BadKernel = 5
    Exception = 255

class Error(Exception):
    def __init__(self, error: int):
        self.error = Errors(error)
        Exception.__init__(self, f'non-success code {self.error}')


def encode(s: str) -> bytes:
    return s.encode(encoding='utf-8', errors='surrogateescape')

def decode(b: bytes) -> str:
    return b.decode(encoding='utf-8', errors='surrogateescape')

def prepare_id(mid: str) -> bytes:
    bmid = encode(mid)
    if len(bmid) != ID_BSIZE:
        raise ValueError('len(bmid) != ID_BSIZE')
    return bmid

def prepare_int(x: int) -> int:
    if not (-128 <= x <= 127):
        raise ValueError('not (-128 <= x <= 127)')
    return x & 0xff

def prepare_matrix(matrix: list[list[int]]) -> bytes:
    if len(matrix) > MAX_SIZE:
        raise ValueError('len(matrix) > MAX_SIZE')
    if len(set(len(row) for row in matrix)) > 1:
        raise ValueError('matrix is not rectangle')
    if len(matrix[0]) > MAX_SIZE:
        raise ValueError('len(matrix[0]) > MAX_SIZE')
    n = len(matrix)
    m = len(matrix[0]) if n > 0 else 0
    res = [0] * n * m
    for j in range(m):
        for i in range(n):
            res[j * n + i] = prepare_int(matrix[i][j])
    return n, m, bytes(res)

def prepare_str(s: str) -> bytes:
    bs = encode(s)
    if len(bs) > MAX_SIZE:
        raise ValueError('len(bs) > MAX_SIZE')
    return bs

def parse(size: int, n: int, m: int, raw: bytes) -> list[list[int]]:
    res = [[0] * m for i in range(n)]
    for j in range(m):
        for i in range(n):
            pos = (j * n + i) * size
            res[i][j] = int.from_bytes(raw[pos:pos + size], 'little', signed=True)
    return res

class Client:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
    async def connect(self):
        self.reader, self.writer = await open_connection(self.host, self.port)
    async def close(self):
        self.writer.close()
        await self.writer.wait_closed()
    def _write_fields(self, *fields : str):
        message = Delimiter.join(fields) + Delimiter
        self.writer.write(encode(message))
    async def _check_status(self):
        code_raw = await self.reader.readexactly(1)
        code = int(code_raw[0])
        if code != 0:
            raise Error(code)
    async def upload(self, matrix: list[list[int]], desc: str, key: str) -> str:
        n, m, bmatrix = prepare_matrix(matrix)
        bdesc = prepare_str(desc)
        bkey = prepare_str(key)

        self._write_fields(Upload, str(n), str(m), str(len(bdesc)), str(len(bkey)))
        self.writer.write(bmatrix)
        self.writer.write(bdesc)
        self.writer.write(bkey)
        await self.writer.drain()

        await self._check_status()
        id_raw = await self.reader.readexactly(ID_BSIZE)
        return decode(id_raw)
    async def download(self, mid: str, key: str) -> (list[list[int]], str):
        bmid = prepare_id(mid)
        bkey = prepare_str(key)

        self._write_fields(Download, str(len(bkey)))
        self.writer.write(bmid)
        self.writer.write(bkey)
        await self.writer.drain()

        await self._check_status()
        sizes = await self.reader.readexactly(3)
        n, m, ndesc = (int(b) for b in sizes)
        matrix_raw = await self.reader.readexactly(n * m)
        matrix = parse(1, n, m, matrix_raw)
        desc_raw = await self.reader.readexactly(ndesc)
        desc = decode(desc_raw)

        return (matrix, desc)
    async def convolution(self, mid: str, kernel: list[list[int]]) -> list[list[int]]:
        bmid = prepare_id(mid)
        kn, km, bkernel = prepare_matrix(kernel)

        self._write_fields(Convolution, str(kn), str(km))
        self.writer.write(bmid)
        self.writer.write(bkernel)
        await self.writer.drain()

        await self._check_status()
        sizes = await self.reader.readexactly(2)
        n, m = (int(b) for b in sizes)
        matrix_raw = await self.reader.readexactly(n * m * 4)
        matrix = parse(4, n, m, matrix_raw)

        return matrix
