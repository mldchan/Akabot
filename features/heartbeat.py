import logging

import aiohttp
import discord
from discord.ext import tasks

from utils.config import get_key


class Heartbeat(discord.Cog):
    def __init__(self) -> None:
        self.interval_cnt = 0
        super().__init__()

        if get_key("Heartbeat_Enabled", "false") == "true":
            self.heartbeat_task.start()
            logging.info("Heartbeat started")
        else:
            logging.warning("Heartbeat is disabled")

    @tasks.loop(seconds=1)
    async def heartbeat_task(self):
        self.interval_cnt += 1
        if self.interval_cnt >= int(get_key("Heartbeat_Interval", '60')):
            self.interval_cnt = 0
            # Send heartbeat
            async with aiohttp.ClientSession() as session:
                method = get_key("Heartbeat_HTTPMethod", 'post').lower()
                if method == "get":
                    await session.get(get_key("Heartbeat_URL", 'https://example.com'))
                elif method == "post":
                    await session.post(get_key("Heartbeat_URL", 'https://example.com'))
                elif method == "put":
                    await session.put(get_key("Heartbeat_URL", 'https://example.com'))
                elif method == "delete":
                    await session.delete(get_key("Heartbeat_URL", 'https://example.com'))
