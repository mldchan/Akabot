import datetime

import discord.ext
import discord.ext.tasks

from database import get_conn


class DbCleanupTask(discord.Cog):
    def __init__(self) -> None:
        super().__init__()

    @discord.ext.tasks.loop(minutes=1)
    async def le_cleanup_task(self):
        now = datetime.datetime.now(datetime.UTC)

        if now.weekday() == 6 and now.hour == 0 and now.minute == 0:
            cur = await get_conn()
            await cur.execute("vacuum")
            await cur.commit()
            await cur.close()

