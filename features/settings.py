import discord
import pymongo

class Settings(discord.Cog):

    def __init__(self, bot: discord.Bot, db: pymongo.MongoClient) -> None:
        self.bot = bot
        self.db = db
        super().__init__()

    @discord.Cog.listener()
    async def on_ready(self):
        print('Settings are ready!')
