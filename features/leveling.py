import os
import json
import asyncio
import datetime
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
        
def get_xp_for_level(level: int):
    current = 0
    xp = 500
    itera = 0
    while current < level:
        if itera >= 10000:
            raise OverflowError('Iteration limit reached.')
        xp *= 2
        current += 1
        itera += 1
        
    return xp

def get_level_for_xp(xp: int):
    current = 0
    level = 0
    itera = 0
    while current < xp:
        if itera >= 10000:
            raise OverflowError('Iteration limit reached.')
        current += 500 * (2 ** level)
        level += 1
        itera += 1
        
    return level

async def update_roles_for_member(guild: discord.Guild, member: discord.Member):
    data = get_file(guild.id, member.id)
    level = get_level_for_xp(data['xp'])
    
    for i in range(1, level + 1): # Add missing roles
        role_id = get_setting(guild.id, f'leveling_reward_{i}', '0')
        if role_id != '0':
            role = guild.get_role(int(role_id))
            if role not in member.roles:
                await member.add_roles(role)
                
    for i in range(level + 1, 100): # Remove excess roles
        role_id = get_setting(guild.id, f'leveling_reward_{i}', '0')
        if role_id != '0':
            role = guild.get_role(int(role_id))
            if role in member.roles:
                await member.remove_roles(role)

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
            if datetime.datetime.now().weekday() in [5, 6]:
                multiplier = str(int(multiplier) * int(weekend_event_multiplier))
        
        data = get_file(msg.guild.id, msg.author.id)
        before_level = get_level_for_xp(data['xp'])
        data['xp'] += len(msg.content) * int(multiplier)
        after_level = get_level_for_xp(data['xp'])
        
        write_file(msg.guild.id, msg.author.id, data)
        await update_roles_for_member(msg.guild, msg.author)
        
        if before_level != after_level:
            msg2 = await msg.channel.send(f'Congratulations, {msg.author.mention}! You have reached level {after_level}!')
            await asyncio.sleep(5)
            await msg2.delete()
        
        
    @discord.slash_command(name='level', description='Get the level of a user')
    @commands_ext.guild_only()
    async def get_level(self, ctx: discord.Interaction, user: discord.User = None):
        user = user or ctx.user
        data = get_file(ctx.guild.id, user.id)
        level = get_level_for_xp(data['xp'])
        
        multiplier = get_setting(ctx.guild.id, 'leveling_xp_multiplier', '1')
        weekend_event = get_setting(ctx.guild.id, 'weekend_event_enabled', 'false')
        weekend_event_multiplier = get_setting(ctx.guild.id, 'weekend_event_multiplier', '2')
        
        final_multiplier = multiplier
        if weekend_event == 'true':
            if datetime.datetime.now().weekday() in [5, 6]:
                final_multiplier = str(int(multiplier) * int(weekend_event_multiplier))
        
        await ctx.response.send_message(f'{user.mention} is level {level}.\nThe multiplier is currently `{str(final_multiplier)}x`.', ephemeral=True)
    
    leveling_subcommand = discord.SlashCommandGroup(name='leveling', description='Leveling settings')
    
    @leveling_subcommand.command(name="list", description="List the leveling settings")
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    async def list_settings(self, ctx: discord.Interaction):
        leveling_xp_multiplier = get_setting(ctx.guild.id, 'leveling_xp_multiplier', '1')
        weekend_event_enabled = get_setting(ctx.guild.id, 'weekend_event_enabled', 'false')
        weekend_event_multiplier = get_setting(ctx.guild.id, 'weekend_event_multiplier', '2')
        
        embed = discord.Embed(title='Leveling settings', color=discord.Color.blurple())
        embed.add_field(name='Leveling multiplier', value=f'`{leveling_xp_multiplier}x`')
        embed.add_field(name='Weekend event', value=weekend_event_enabled)
        embed.add_field(name='Weekend event multiplier', value=f'`{weekend_event_multiplier}x`')
        
        await ctx.response.send_message(embed=embed, ephemeral=True)
    
    @leveling_subcommand.command(name='multiplier', description='Set the leveling multiplier')
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @discord.option(name="multiplier", description="The multiplier to set", type=int)
    async def set_multiplier(self, ctx: discord.Interaction, multiplier: int):
        set_setting(ctx.guild.id, 'leveling_xp_multiplier', str(multiplier))
        await ctx.response.send_message(f'Successfully set the leveling multiplier to {multiplier}.', ephemeral=True)

    @leveling_subcommand.command(name='weekend_event', description='Set the weekend event')
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @discord.option(name="enabled", description="Whether the weekend event is enabled", type=bool)
    async def set_weekend_event(self, ctx: discord.Interaction, enabled: bool):
        set_setting(ctx.guild.id, 'weekend_event_enabled', str(enabled).lower())
        await ctx.response.send_message(f'Successfully set the weekend event to {enabled}.', ephemeral=True)
    
    @leveling_subcommand.command(name='weekend_event_multiplier', description='Set the weekend event multiplier')
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @discord.option(name="weekend_event_multiplier", description="The multiplier to set", type=int)
    async def set_weekend_event_multiplier(self, ctx: discord.Interaction, weekend_event_multiplier: int):
        set_setting(ctx.guild.id, 'weekend_event_multiplier', str(weekend_event_multiplier))
        await ctx.response.send_message(f'Successfully set the weekend event multiplier to {weekend_event_multiplier}.', ephemeral=True)
    
    @leveling_subcommand.command(name='set_reward', description='Set a role for a level')
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @discord.option(name="level", description="The level to set the reward for", type=int)
    @discord.option(name='role', description='The role to set', type=discord.Role)
    async def set_reward(self, ctx: discord.Interaction, level: int, role: discord.Role):
        set_setting(ctx.guild.id, f'leveling_reward_{level}', str(role.id))
        await ctx.response.send_message(f'Successfully set the reward for level {level} to {role.mention}.', ephemeral=True)
        
    @leveling_subcommand.command(name='remove_reward', description='Remove a role for a level')
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @discord.option(name="level", description="The level to remove the reward for", type=int)
    async def remove_reward(self, ctx: discord.Interaction, level: int):
        set_setting(ctx.guild.id, f'leveling_reward_{level}', '0')
        await ctx.response.send_message(f'Successfully removed the reward for level {level}.', ephemeral=True)
