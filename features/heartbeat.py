import discord
import requests
import logging

from utils.config import get_key
from discord.ext import tasks


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
            logging.info("Sending heartbeat")
            self.interval_cnt = 0
            # Send heartbeat
            if get_key("Heartbeat_HTTPMethod", 'post') == "get":
                requests.get(get_key("Heartbeat_URL", 'https://example.com'))
            elif get_key("Heartbeat_HTTPMethod", 'post') == "post":
                requests.post(get_key("Heartbeat_URL", 'https://example.com'))
            elif get_key("Heartbeat_HTTPMethod", 'post') == "put":
                requests.put(get_key("Heartbeat_URL", 'https://example.com'))
            elif get_key("Heartbeat_HTTPMethod", 'post') == "delete":
                requests.delete(get_key("Heartbeat_URL", 'https://example.com'))

            logging.info("Heartbeat sent")
