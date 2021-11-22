import tempfile
import time

import pytest

from users import User, UsersDB, AuthenticationError


@pytest.fixture()
def tempdir():
    with tempfile.TemporaryDirectory() as d:
        yield d


def test_user_creation():
    user = User(username="foo", password="abc")
    assert user.username == "foo"
    assert len(user.hash) == 64  # SHA256
    assert user.timestamp % 60 == 0
    assert time.monotonic() - user.timestamp <= 60
    assert time.monotonic() - user.timestamp > 0
    assert user.slot is None


def test_user_serialization():
    user1 = User(username="foo", password="secret")
    user2 = User.deserialize(repr(user1))

    assert user1.username == user2.username
    assert user1.hash == user2.hash
    assert user1.slot == user2.slot
    assert user1.timestamp == user2.timestamp


@pytest.mark.asyncio
async def test_users_db_auth(tempdir):
    db = UsersDB(folder=tempdir)
    await db.add("foo", "secret")

    user = db.authenticate("foo", "secret")
    assert user is not None
    assert user.username == "foo"

    with pytest.raises(AuthenticationError):
        db.authenticate("foo", "wrong")

    with pytest.raises(AuthenticationError):
        db.authenticate("unknown", "secret")


@pytest.mark.asyncio
async def test_users_db_store_load(tempdir):
    db = UsersDB(folder=tempdir)
    await db.add("foo", "secret")

    db = UsersDB(folder=tempdir)
    await db.load()

    user = db.authenticate("foo", "secret")
    assert user is not None
