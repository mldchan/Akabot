import discord
import os
import json
import datetime
from discord.ext import commands as commands_ext
from discord.ext import tasks

def read_file(guild_id: str, channel_id: str) -> dict | None:
    if not os.path.exists('data'):
        os.mkdir('data')
    if not os.path.exists('data/chatsummary'):
        os.mkdir('data/chatsummary')
    if not os.path.exists(f'data/chatsummary/{guild_id}'):
        os.mkdir(f'data/chatsummary/{guild_id}')
    if not os.path.exists(f'data/chatsummary/{guild_id}/{channel_id}.json'):
        return None
    
    with open(f'data/chatsummary/{guild_id}/{channel_id}.json', 'r') as f:
        return json.load(f)
    
def write_file(guild_id: str, channel_id: str, data: dict):
    if not os.path.exists('data'):
        os.mkdir('data')
    if not os.path.exists('data/chatsummary'):
        os.mkdir('data/chatsummary')
    if not os.path.exists(f'data/chatsummary/{guild_id}'):
        os.mkdir(f'data/chatsummary/{guild_id}')
    with open(f'data/chatsummary/{guild_id}/{channel_id}.json', 'w') as f:
        json.dump(data, f)
        
def delete_file(guild_id: str, channel_id: str):
    if not os.path.exists('data'):
        os.mkdir('data')
    if not os.path.exists('data/chatsummary'):
        os.mkdir('data/chatsummary')
    if not os.path.exists(f'data/chatsummary/{guild_id}'):
        os.mkdir(f'data/chatsummary/{guild_id}')
    if os.path.exists(f'data/chatsummary/{guild_id}/{channel_id}.json'):
        os.unlink(f'data/chatsummary/{guild_id}/{channel_id}.json')
        

class ChatSummary(discord.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        super().__init__()
        self.bot = bot
        
    @discord.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is None:
            return
        data = read_file(str(message.guild.id), str(message.channel.id))
        
        if data is None:
            return
        
        data['messages'] += 1
        data['owo'] += len(message.content.split('owo')) - 1
        data['owo'] += len(message.content.split('uwu')) - 1
        
        data['nya'] += len(message.content.split('meow')) - 1
        data['nya'] += len(message.content.split('nya')) - 1
        
        data[':3'] += len(message.content.split(':3')) - 1
        
        if str(message.author.id) not in data['members']:
            data['members'][str(message.author.id)] = 0
        
        data['members'][str(message.author.id)] += 1
        
        write_file(message.guild.id, message.channel.id, data)
        
    @tasks.loop(minutes=1)
    async def summarize(self):
        now = datetime.datetime.utcnow()
        if now.hour != 0 or now.minute != 0:
            return
        
        for i in os.listdir('data/chatsummary'):
            guild = self.bot.get_guild(int(i))
            for j in os.listdir(f'data/chatsummary/{i}'):
                j = int(j.split('.')[0])
                data = read_file(i, j)
                if data is None:
                    continue
                
                channel = guild.get_channel(j)
                if channel is None:
                    continue
                
                embed = discord.Embed(title="Chat Summary")
                embed.add_field(name="Messages", value=str(data['messages']))
                embed.add_field(name="OwOs", value=str(data['owo']))
                embed.add_field(name="Nya~'s", value=str(data['nya']))
                embed.add_field(name=":3's", value=str(data[':3']))
                
                desc = ""
                
                for k in range(max(len(data['members']), 5)):
                    members = sorted(data['members'].items(), key=lambda item: item[1])
                    member = guild.get_member(members[0])
                    if member is None:
                        continue
                    
                    desc += f"{k + 1}. {member.display_name} with {members[1]} messages\n"
                    
                embed.description = desc
                
                await channel.send(embed=embed)
                
                write_file(i, str(j), {'messages': 0, 'members': {}, 'owo': 0, 'nya': 0, ':3': 0})
                    
        
    chat_summary_subcommand = discord.SlashCommandGroup(name='chatsummary', description='Chat summary')
    
    @chat_summary_subcommand.command(name="add", description="Add a channel to count to chat summary")
    @commands_ext.guild_only()
    @commands_ext.has_permissions(manage_guild=True)
    async def command_add(self, ctx: discord.Interaction, channel: discord.TextChannel):
        data = read_file(ctx.guild.id, channel.id)
        if data is None:
            write_file(ctx.guild.id, channel.id, {'messages': 0, 'members': {}, 'owo': 0, 'nya': 0, ':3': 0})
            await ctx.response.send_message('Added channel to counting, from now.', ephemeral=True)
            return
        
        await ctx.response.send_message('This channel is already being counted. To remove it, run `/chatsummary remove`.', ephemeral=True)
        
    @chat_summary_subcommand.command(name="remove", description="Remove a channel from being counted to chat summary")
    @commands_ext.guild_only()
    @commands_ext.has_permissions(manage_guild=True)
    async def command_remove(self, ctx: discord.Interaction, channel: discord.TextChannel):
        data = read_file(ctx.guild.id, channel.id)
        if data is not None:
            delete_file(ctx.guild.id, channel.id)
            await ctx.response.send_message('Removed channel from counting, along with the data.', ephemeral=True)
            return
        
        await ctx.response.send_message('This channel is already not being counted.', ephemeral=True)
        