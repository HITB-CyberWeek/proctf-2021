import asyncio
import hashlib
import logging
import os.path
import re
import time
import typing

from aiofile import async_open

USER_TTL_SECONDS = 20 * 60

username_re = re.compile("^[a-zA-Z0-9_-]+$")


def timestamp():
    return int(time.monotonic() / 60) * 60


def hash_password(password: str):
    return hashlib.sha256(password.encode()).hexdigest()


class UserAlreadyExists(Exception):
    pass


class AuthenticationError(Exception):
    pass


class User:
    def __init__(self, username: str, password: typing.Optional[str] = None, hash: typing.Optional[str] = None):
        self.username = username
        if password is not None:
            self.hash = hash_password(password)
        if hash is not None:
            self.hash = hash
        self.timestamp = timestamp()
        self.slot = None

    def is_expired(self) -> bool:
        return timestamp() - self.timestamp > USER_TTL_SECONDS

    @staticmethod
    def deserialize(s: str) -> "User":
        tokens = s.strip().split(":")
        if len(tokens) != 4:
            raise ValueError("Invalid user data: {!r}.".format(s))
        user = User(username=tokens[0], hash=tokens[1])
        user.timestamp = int(tokens[2])
        if tokens[3] != "None":
            user.slot = int(tokens[3])
        return user

    def __repr__(self):
        return "{}:{}:{}:{}".format(self.username, self.hash, self.timestamp, self.slot)


class UsersDB:
    def __init__(self, folder: str):
        self._lock = asyncio.Lock()
        self._folder = folder
        if not os.path.isdir(folder):
            os.makedirs(folder)
        self._data = dict()  # username -> [hash, slot, timestamp]

    async def load(self):
        async with self._lock:
            for subdir in os.listdir(self._folder):
                for file in os.listdir(os.path.join(self._folder, subdir)):
                    fullname = os.path.join(self._folder, subdir, file)
                    try:
                        user = await self._read(fullname)
                    except ValueError:
                        continue
                    if not user.is_expired():
                        self._data[user.username] = user

    async def add(self, username: str, password: str):
        if not username_re.match(username):
            raise ValueError("Wrong characters in username.")
        async with self._lock:
            if username in self._data:
                raise UserAlreadyExists()
            user = User(username, password)
            self._data[username] = user
            await self._write(user)
        return user

    async def update(self, user: User):
        await self._write(user)

    def authenticate(self, username: str, password: str) -> User:
        user = self._data.get(username)  # type: User
        if user is None:
            raise AuthenticationError("Invalid username or password")
        if hash_password(password) != user.hash:
            raise AuthenticationError("Invalid username or password")
        if user.is_expired():
            raise AuthenticationError("Trial account has been blocked")
        return user

    def count(self):
        return len(self._data)

    async def _write(self, user: User) -> None:
        dirname = os.path.join(self._folder, str(user.timestamp))
        os.makedirs(dirname, exist_ok=True)
        filename = os.path.join(dirname, user.username)
        async with async_open(filename, "w") as f:
            await f.write(repr(user) + "\n")

    async def _read(self, filename: str) -> User:
        async with async_open(filename, "r") as f:
            data = await f.readline()
            return User.deserialize(data)
