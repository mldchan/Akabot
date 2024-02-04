import discord
from discord import commands as discord_commands
from discord.ext import commands as discord_commands_ext
from discord.ext import pages as pages_ext
import pymongo


class Settings(discord.Cog):

    def __init__(self, bot: discord.Bot, db: pymongo.MongoClient) -> None:
        self.bot = bot
        self.db = db
        super().__init__()
        
    string_keys = ['welcome_title', 'welcome_message', 'goodbye_message', 'goodbye_title']
    channel_keys = ['welcome_channel', 'goodbye_channel']
    boolean_keys = ['welcome_enabled', 'goodbye_enabled']

    settings = discord_commands.SlashCommandGroup(name='settings', description='Manage the settings of the bot')
    
    @settings.sub_command(name='get', description='Get a setting')
    async def get_setting(self, ctx: discord_commands.Context, key: str) -> None:
        server_id = ctx.guild.id
        value = await self.get_setting(server_id, key, 'None')
        await ctx.send(f'The value of {key} is {value}')
