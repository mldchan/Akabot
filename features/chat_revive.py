import os
import json
import time
import discord
from discord.ext import commands as commands_ext
from discord.ext import tasks
from utils.blocked import is_blocked

def read_file(server_id: int):
    if not os.path.exists('data'):
        os.mkdir('data')
    if not os.path.exists('data/chatrevive'):
        os.mkdir('data/chatrevive')
    if not os.path.exists(f'data/chatrevive/{str(server_id)}.json'):
        with open(f'data/chatrevive/{str(server_id)}.json', 'w', encoding='utf8') as f:
            json.dump({}, f)
    with open(f'data/chatrevive/{str(server_id)}.json', 'r', encoding='utf8') as f:
        settings = json.load(f)
    return settings

def write_file(server_id: int, settings):
    if not os.path.exists('data'):
        os.mkdir('data')
    if not os.path.exists('data/chatrevive'):
        os.mkdir('data/chatrevive')
    if os.path.exists(f'data/chatrevive/{str(server_id)}.json'):
        os.remove(f'data/chatrevive/{str(server_id)}.json')
    with open(f'data/chatrevive/{str(server_id)}.json', 'w', encoding='utf8') as f:
        json.dump(settings, f)


class ChatRevive(discord.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        self.revive_channels.start()

    @discord.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        
        settings = read_file(message.guild.id)
        if message.channel.id in settings:
            settings[message.channel.id]['last_message'] = time.time()
            settings[message.channel.id]['revived'] = False

    @tasks.loop(minutes=1)
    async def revive_channels(self):
        for guild in self.bot.guilds:
            settings = read_file(guild.id)
            for revive_channel in settings:
                if settings[revive_channel]['revived']:
                    continue
                
                if time.time() - settings[revive_channel]['last_message'] > settings[revive_channel]['revival_time']:
                    role = guild.get_role(settings[revive_channel]['role'])
                    if role is None:
                        continue
                    
                    channel = guild.get_channel(int(revive_channel))
                    if channel is None:
                        continue
                    await channel.send(f'{role.mention}, this channel has been inactive for a while.')
                    settings[revive_channel]['revived'] = True
                    
            write_file(guild.id, settings)
                    
                    
    chat_revive_subcommand = discord.SlashCommandGroup(name='chatrevive', description='Revive channels')
    
    @chat_revive_subcommand.command(name="set", description="Set revive settings for a channel")
    @commands_ext.guild_only()
    @commands_ext.has_permissions(manage_guild=True)
    @is_blocked()
    async def set_revive_settings(self, ctx: discord.Interaction, channel: discord.TextChannel, revival_minutes: int, revival_role: discord.Role):
        settings = read_file(ctx.guild.id)
        settings[str(channel.id)] = {'last_message': time.time(), 'revived': False, 'role': revival_role.id, 'revival_time': revival_minutes * 60}
        write_file(ctx.guild.id, settings)
        await ctx.response.send_message(f'Successfully set revive settings for {channel.mention}.', ephemeral=True)
        
    @chat_revive_subcommand.command(name="remove", description="List the revive settings")
    @commands_ext.guild_only()
    @commands_ext.has_permissions(manage_guild=True)
    @is_blocked()
    async def remove_revive_settings(self, ctx: discord.Interaction, channel: discord.TextChannel):
        settings = read_file(ctx.guild.id)
        del settings[str(channel.id)]
        write_file(ctx.guild.id, settings)
        await ctx.response.send_message(f'Successfully removed revive settings for {channel.mention}.', ephemeral=True)
        
    @chat_revive_subcommand.command(name="list", description="List the revive settings")
    @commands_ext.guild_only()
    @commands_ext.has_permissions(manage_guild=True)
    @is_blocked()
    async def list_revive_settings(self, ctx: discord.Interaction, channel: discord.TextChannel):
        settings = read_file(ctx.guild.id)
        
        if not str(channel.id) in settings:
            await ctx.response.send_message(f'There are no revive settings for {channel.mention}.', ephemeral=True)
            return
        
        embed = discord.Embed(title=f'Revive settings for {channel.name}', color=discord.Color.blurple())
        embed.add_field(name='Role', value=discord.utils.get(ctx.guild.roles, id=settings[str(channel.id)]['role']).mention)
        embed.add_field(name='Revival time (seconds)', value=settings[str(channel.id)]['revival_time'])
        
        await ctx.response.send_message(embed=embed, ephemeral=True)
