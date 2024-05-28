import discord

import discord.ext
import discord.ext.tasks

import datetime

from database import conn

class DbCleanupTask(discord.Cog):
    def __init__(self) -> None:
        super().__init__()

    @discord.ext.tasks.loop(minutes=1)
    async def le_cleanup_task(self):
        now = datetime.datetime.now(datetime.UTC)

        if now.weekday() == 6 and now.hour == 0 and now.minute == 0:
            print("Cleaning up db...")

            cur = conn.cursor()
            cur.execute("vacuum")
            cur.close()
            conn.commit()

            print("Cleaned up DB")

