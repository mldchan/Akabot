import discord
from discord import commands as discord_commands
from discord.ext import commands as discord_commands_ext
import pymongo
import uuid
from datetime import datetime
import math

class Settings(discord.Cog):

    def __init__(self, bot: discord.Bot, db: pymongo.MongoClient) -> None:
        self.bot = bot
        self.db = db
        super().__init__()

    @discord.slash_command()
    @discord_commands.guild_only()
    @discord_commands_ext.has_guild_permissions(manage_guild=True)
    @discord_commands_ext.cooldown(1, 120, discord_commands_ext.BucketType.guild)
    async def settings(self, ctx: discord.Interaction):
        unix_timestamp = int(round((datetime.now() - datetime(1970, 1, 1)).total_seconds(), 0))
        token = uuid.uuid4().hex

        self.db\
            .get_database('FemboyBot')\
            .get_collection('WebTokens')\
            .delete_many({'expires': {'$lt': unix_timestamp}}) # This deletes expired tokens, I love this database

        self.db \
            .get_database('FemboyBot') \
            .get_collection('WebTokens') \
            .insert_one({
            'user_name': ctx.user.name,
            'user_id': ctx.user.id,
            'guild_name': ctx.guild.name,
            'token': token,
            'expires': unix_timestamp + 3600
        })

        await ctx.response.send_message(content=f'You can edit server settings here: http://localhost:3000/settings/{token} .\nThis link will expire in 1 hour.', ephemeral=True)
