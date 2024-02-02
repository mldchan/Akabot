
import discord
import pymongo

class Welcoming(discord.Cog):
    def __init__(self, bot: discord.Bot, db: pymongo.MongoClient) -> None:
        self.bot = bot
        self.db = db
    
    @discord.Cog.listener()
    async def on_member_join(member: discord.Member):
        pass

    @discord.Cog.listener()
    async def on_member_remove(member: discord.Member):
        pass
