import discord
import requests
import logging

class HeartbeatData():
    def __init__(self, *args, **kwargs) -> None:
        self.enabled = kwargs.get("enabled", False)
        self.url = kwargs.get("url", None)
        self.method = kwargs.get("method", None)
        self.interval = kwargs.get("interval", None)
        pass

    enabled: bool = False
    url: str = None,
    method: str = None
    interval: int = None

class Heartbeat(discord.Cog):
    def __init__(self, data: HeartbeatData) -> None:
        self.enabled = data.enabled
        self.url = data.url
        self.method = data.method
        self.interval = data.interval
        self.interval_cnt = 0
        super().__init__()

        if self.enabled:
            self.heartbeat_task.start()
            logging.info("Heartbeat started")
        else:
            logging.warning("Heartbeat is disabled")


    @discord.ext.tasks.loop(seconds=1)
    async def heartbeat_task(self):
        self.interval_cnt += 1
        if self.interval_cnt >= self.interval:
            logging.info("Sending heartbeat")
            self.interval_cnt = 0
            # Send heartbeat
            if self.method == "get":
                requests.get(self.url)
            elif self.method == "post":
                requests.post(self.url)
            elif self.method == "put":
                requests.put(self.url)
            elif self.method == "delete":
                requests.delete(self.url)

            logging.info("Heartbeat sent")
