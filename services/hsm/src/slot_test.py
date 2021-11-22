import os

import pytest

from slot import LastSlotStorage, LAST_SLOT_FILE


@pytest.mark.asyncio
async def test_read_nonexistent():
    try:
        os.unlink(LAST_SLOT_FILE)
    except FileNotFoundError:
        pass
    s = LastSlotStorage()
    value = await s.read()
    assert value < 0


@pytest.mark.asyncio
async def test_write_read():
    s = LastSlotStorage()
    async with s.lock:
        await s.write(123)
    value = await s.read()
    assert value == 123
