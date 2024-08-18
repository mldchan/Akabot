import discord
import requests
from discord.ext import tasks

from utils.config import get_key

SEND_SECONDS = int(get_key("Send_Server_Count_Seconds", "0"))
SEND_MINUTES = int(get_key("Send_Server_Count_Minutes", "0"))
SEND_HOURS = int(get_key("Send_Server_Count_Hours", "0"))

SEND = get_key("Send_Server_Count_API", "false") == "true"
SEND_METHOD = get_key("Send_Server_Count_Method", "post")
SEND_URL = get_key("Send_Server_Count_URL", "")

TOPGG_SEND = get_key("TopGG_Send", "false") == "true"
TOPGG_TOKEN = get_key("TopGG_Token", "")
TOPGG_BOT_ID = get_key("TopGG_Bot_ID", "")


class SendServerCount(discord.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @discord.Cog.listener()
    async def on_ready(self):
        if SEND:
            self.send_server_count.start()
        if TOPGG_SEND:
            self.send_topgg_server_count.start()

    @tasks.loop(seconds=SEND_SECONDS, minutes=SEND_MINUTES, hours=SEND_HOURS)
    async def send_server_count(self):
        if SEND_METHOD == "get":
            requests.get(SEND_URL, params={"count": len(self.bot.guilds)})
        elif SEND_METHOD == "post":
            requests.post(SEND_URL, json={"count": len(self.bot.guilds)})
        elif SEND_METHOD == "put":
            requests.put(SEND_URL, json={"count": len(self.bot.guilds)})
        else:
            raise ValueError("Invalid method")

    @tasks.loop(seconds=SEND_SECONDS, minutes=SEND_MINUTES, hours=SEND_HOURS)
    async def send_topgg_server_count(self):
        headers = {
            "Authorization": f"Bearer {TOPGG_TOKEN}"
        }

        requests.post(f"https://top.gg/api/bots/{TOPGG_BOT_ID}/stats", headers=headers, json={"server_count": len(self.bot.guilds)})
