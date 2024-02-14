import os
import json
import discord
from discord.ext import commands as commands_ext

from utils.settings import get_setting, set_setting

def get_file(guild_id: int, user_id: int) -> dict:
    if not os.path.exists('data'):
        os.mkdir('data')
    if not os.path.exists('data/leveling'):
        os.mkdir('data/leveling')
    if not os.path.exists(f'data/leveling/{str(guild_id)}'):
        os.mkdir(f'data/leveling/{str(guild_id)}')
    if not os.path.exists(f'data/leveling/{str(guild_id)}/{str(user_id)}.json'):
        with open(f'data/leveling/{str(guild_id)}/{str(user_id)}.json', 'w', encoding='utf8') as f:
            json.dump({'xp': 0}, f)
    with open(f'data/leveling/{str(guild_id)}/{str(user_id)}.json', 'r', encoding='utf8') as f:
        return json.load(f)
    
def write_file(guild_id: int, user_id: int, data: dict) -> None:
    if not os.path.exists('data'):
        os.mkdir('data')
    if not os.path.exists('data/leveling'):
        os.mkdir('data/leveling')
    if not os.path.exists(f'data/leveling/{str(guild_id)}'):
        os.mkdir(f'data/leveling/{str(guild_id)}')
    if os.path.exists(f'data/leveling/{str(guild_id)}/{str(user_id)}.json'):
        os.remove(f'data/leveling/{str(guild_id)}/{str(user_id)}.json')
    with open(f'data/leveling/{str(guild_id)}/{str(user_id)}.json', 'w', encoding='utf8') as f:
        json.dump(data, f)

class Leveling(discord.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot
        super().__init__()
    
    @discord.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot:
            return
        
        multiplier = get_setting(msg.guild.id, 'leveling_xp_multiplier', '1')
        weekend_event = get_setting(msg.guild.id, 'weekend_event_enabled', 'false')
        weekend_event_multiplier = get_setting(msg.guild.id, 'weekend_event_multiplier', '2')
        if weekend_event == 'true':
            if msg.created_at.weekday() in [5, 6]:
                multiplier = str(int(multiplier) * int(weekend_event_multiplier))
        
        data = get_file(msg.guild.id, msg.author.id)
        data['xp'] += len(msg.content) * multiplier
        write_file(msg.guild.id, msg.author.id, data)
    
    leveling_subcommand = discord.SlashCommandGroup(name='leveling', description='Leveling settings')
    
    @leveling_subcommand.command(name='multiplier', description='Set the leveling multiplier')
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @discord.option(name="multiplier", description="The multiplier to set", type=int)
    async def set_multiplier(self, ctx: discord.Interaction, multiplier: int):
        set_setting(ctx.guild.id, 'leveling_xp_multiplier', str(multiplier))
        await ctx.response.send_message(f'Successfully set the leveling multiplier to {multiplier}.')

    @leveling_subcommand.command(name='weekend_event', description='Set the weekend event')
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @discord.option(name="enabled", description="Whether the weekend event is enabled", type=bool)
    async def set_weekend_event(self, ctx: discord.Interaction, enabled: bool):
        set_setting(ctx.guild.id, 'weekend_event_enabled', str(enabled).lower())
        await ctx.response.send_message(f'Successfully set the weekend event to {enabled}.')
    
    @leveling_subcommand.command(name='weekend_event_multiplier', description='Set the weekend event multiplier')
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @discord.option(name="weekend_event_multiplier", description="The multiplier to set", type=int)
    async def set_weekend_event_multiplier(self, ctx: discord.Interaction, weekend_event_multiplier: int):
        set_setting(ctx.guild.id, 'weekend_event_multiplier', str(weekend_event_multiplier))
        await ctx.response.send_message(f'Successfully set the weekend event multiplier to {weekend_event_multiplier}.')
    