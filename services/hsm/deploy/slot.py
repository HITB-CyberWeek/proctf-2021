import asyncio

from aiofile import async_open

LAST_SLOT_FILE = "state/last_slot"  # Contains last used slot.


class LastSlotStorage:
    def __init__(self):
        self.lock = asyncio.Lock()

    # Must be called under one lock (self.lock) with GENERATE command.
    async def write(self, value: int) -> None:
        async with async_open(LAST_SLOT_FILE, "w") as f:
            await f.write("{}\n".format(value))

    # Called once at service startup.
    async def read(self) -> int:
        try:
            async with async_open(LAST_SLOT_FILE, "r") as f:
                return int((await f.readline()).strip())
        except FileNotFoundError:
            return -1
