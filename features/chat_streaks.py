import discord
import time
import os
import json

from discord.ext import commands as commands_ext

from utils.settings import get_setting, set_setting 

class ChatStreakStorage():
    """Chat Streaks Storage.
    Every member has 24 hours before their streak gets reset.
    If their streak day changes to the next day without expiring, they get congratulated.
    """
    guilds = {}
    
    def set_streak(self, guild_id: int, member_id: int) -> tuple[str, int, int]:
        """Set streak

        Args:
            guild_id (int): Guild ID
            member_id (int): Member ID

        Returns:
            str: The state of the streak
        """
        if not guild_id in self.guilds:
            self.guilds[guild_id] = {}
        
        if not member_id in self.guilds[guild_id]:
            self.guilds[guild_id][member_id] = {'last_message': time.time(), 'start_time': time.time()}
            return ("started", 0, 0)
        
        if time.time() - self.guilds[guild_id][member_id]['last_message'] > 86400:
            (streak, _) = divmod(time.time() - self.guilds[guild_id][member_id]['start_time'], 86400)
            self.guilds[guild_id][member_id]['streak'] = 0
            self.guilds[guild_id][member_id]['start_time'] = time.time()
            return ("expired", streak, 0)
        
        (before_update, _) = divmod(self.guilds[guild_id][member_id]['last_message'] - self.guilds[guild_id][member_id]['start_time'], 86400)
        self.guilds[guild_id][member_id]['last_message'] = time.time()
        (after_update, _) = divmod(self.guilds[guild_id][member_id]['last_message']  - self.guilds[guild_id][member_id]['start_time'], 86400)
        
        if before_update != after_update:
            return ("updated", before_update, after_update)
        
        return ("stayed", after_update, 0)
    
    def reset_streak(self, guild_id: int, member_id: int) -> None:
        """Reset streak

        Args:
            guild_id (int): Guild ID
            member_id (int): Member ID
        """
        if not guild_id in self.guilds:
            self.guilds[guild_id] = {}
        
        if not member_id in self.guilds[guild_id]:
            self.guilds[guild_id][member_id] = {'last_message': time.time(), 'start_time': time.time()}
            return
        
        self.guilds[guild_id][member_id] = {'last_message': time.time(), 'start_time': time.time()}
    
    def save(self):
        for i in self.guilds:
            guild = self.guilds[i]
            if not os.path.exists('data'):
                os.mkdir('data')
            if not os.path.exists('data/chatstreaks'):
                os.mkdir('data/chatstreaks')
            with open(f'data/chatstreaks/{i}.json', 'w', encoding='utf8') as f:
                json.dump(guild, f)
            
    def load(self):
        if not os.path.exists('data/chatstreaks'):
            os.mkdir('data/chatstreaks')
        
        for i in os.listdir('data/chatstreaks'):
            i = i.split('.')[0]
            with open(f'data/chatstreaks/{i}.json', 'r', encoding='utf8') as f:
                self.guilds[int(i)] = json.load(f)
            
    

class ChatStreaks(discord.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        super().__init__()
        self.bot = bot
        self.streaks = ChatStreakStorage()
        self.streaks.load()
        
    @discord.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        
        (state, streak, new_day) = self.streaks.set_streak(message.guild.id, message.author.id)
        
        if get_setting(message.guild.id, 'chat_streak_alerts', 'true') == 'true':
            if state == "expired":
                await message.channel.send(f'Your streak of {streak} days has expired :<')
            
            if state == "updated":
                await message.channel.send(f'You\'re now on streak {streak} -> {new_day}! Keep it up :3')
        
        self.streaks.save()
    
    
    streaks_subcommand = discord.SlashCommandGroup(name='streaks', description='Manage the chat streaks')
    
    @streaks_subcommand.command(name="alerts", description="Show/hide the chat streak alerts")
    @commands_ext.guild_only()
    @commands_ext.has_permissions(manage_guild=True)
    async def toggle_alerts(self, ctx: discord.Interaction, value: bool):
        set_setting(ctx.guild.id, 'chat_streak_alerts', value)
        await ctx.response.send_message('Succcessfully turned on chat streaks' if value else 'Successfully turned off chat streaks', ephemeral=True)
    
    @streaks_subcommand.command(name="list", description="List the chat streak options.")
    @commands_ext.guild_only()
    @commands_ext.has_permissions(manage_guild=True)
    async def list_settings(self, ctx: discord.Interaction):
        alerts = get_setting(ctx.guild.id, 'chat_streak_alerts', 'true')
        
        embed = discord.Embed(title='Chat Streak settings', color=discord.Color.blurple())
        embed.add_field(name='Chat Streak Alerts', value=alerts)
        
        await ctx.response.send_message(embed=embed, ephemeral=True)
        
    @streaks_subcommand.command(name="reset", description="Reset streak for a specific user")
    @commands_ext.guild_only()
    @commands_ext.has_permissions(manage_guild=True)
    @discord.option(name='user', description='The user to reset the streak for', type=discord.Member)
    async def reset_streak(self, ctx: discord.Interaction, user: discord.Member):
        self.streaks.reset_streak(ctx.guild.id, user.id)
        await ctx.response.send_message(f'Successfully reset the streak for {user.mention}.', ephemeral=True)
        
    @streaks_subcommand.command(name="streak", description="Get someone's streak, to get yours, /streak.")
    @commands_ext.guild_only()
    @commands_ext.has_permissions(manage_guild=True)
    @discord.option(name='user', description='The user to get the streak for', type=discord.Member)
    async def get_user_streak(self, ctx: discord.Interaction, user: discord.Member):
        (_, streak, _) = self.streaks.set_streak(ctx.guild.id, user.id)
        await ctx.response.send_message(f'{user.mention}\'s current streak is {streak} days.', ephemeral=True)

    @discord.slash_command(name='streak', description='Get your current streak')
    async def get_streak(self, ctx: discord.Interaction):
        (_, _, new_day) = self.streaks.set_streak(ctx.guild.id, ctx.user.id)
        await ctx.response.send_message(f'Your current streak is {new_day} days.', ephemeral=True)