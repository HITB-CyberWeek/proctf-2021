from dataclasses import dataclass


@dataclass
class InputStream:
    s: bytes
    index: int = 0

    def read(self, n: int) -> bytes:
        result = self.s[self.index:self.index + n]
        self.index += n
        return result

    def read_byte(self) -> int:
        return self.read(1)[0]

    @property
    def next(self) -> int:
        return self.s[self.index]

    @property
    def has_next(self) -> bool:
        return self.index < len(self.s)


@dataclass
class OutputStream:
    s: bytes = b""

    def write(self, values: bytes):
        self.s += values