import datetime
import os.path
import time

import discord

from utils.config import get_key
from discord.ext import tasks
from utils.generic import pretty_time_delta, pretty_time


class PowerOutageAnnouncement(discord.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @discord.Cog.listener()
    async def on_ready(self):
        if not os.path.exists("data/current_time.txt"):
            self.save_current_time.start()
            return

        channel_id = get_key("PowerOutageAnnouncements_ChannelID", "0")
        with open("data/current_time.txt", "r") as f:
            current_time = float(f.read())
        with open("configs/power_outage_announcement_message.txt", "r") as f:
            power_outage_message = str(f.read())

        channel = self.bot.get_channel(int(channel_id))
        if not channel:
            self.save_current_time.start()
            return

        # format things like {pretty_time} and other things into the message
        power_outage_message = power_outage_message.replace("{pretty_time}",
                                                            pretty_time_delta(time.time() - current_time))
        power_outage_message = power_outage_message.replace("{outage_time}", pretty_time(current_time))
        power_outage_message = power_outage_message.replace("{now_time}", pretty_time(time.time()))

        await channel.send(power_outage_message)
        self.save_current_time.start()

    @tasks.loop(minutes=1)
    async def save_current_time(self):
        with open("data/current_time.txt", "w") as f:
            f.write(str(time.time()))
