import datetime

import discord
from discord.ext import commands as commands_ext

from utils.analytics import analytics
from utils.blocked import is_blocked


def pretty_time_delta(seconds: int):
    sign_string = '-' if seconds < 0 else ''
    seconds = abs(int(seconds))
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days > 0:
        return '%s%d days %d hours %d minutes and %d seconds' % (sign_string, days, hours, minutes, seconds)
    elif hours > 0:
        return '%s%d hours %d minutes and %d seconds' % (sign_string, hours, minutes, seconds)
    elif minutes > 0:
        return '%s%d minutes and %d seconds' % (sign_string, minutes, seconds)
    else:
        return '%s%d seconds' % (sign_string, seconds)


class Moderation(discord.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @discord.slash_command(name='kick', description='Kick a user from the server')
    @commands_ext.guild_only()
    @commands_ext.has_permissions(kick_members=True)
    @discord.option(name='user', description='The user to kick', type=discord.Member)
    @discord.option(name='reason', description='The reason for kicking', type=str)
    @discord.option(name='send_dm', description='Send a DM to the user', type=bool, required=False, default=True)
    @is_blocked()
    @analytics("kick")
    async def kick_user(self, ctx: discord.ApplicationContext, user: discord.Member, reason: str, send_dm: bool = True):

        if user.id == self.bot.user.id:  # Check if the user is the bot
            await ctx.response.send_message('I cannot kick myself.', ephemeral=True)
            return

        if user.id == ctx.user.id:  # Check if the user is the author
            await ctx.response.send_message('You cannot kick yourself.', ephemeral=True)
            return

        if user.top_role >= ctx.user.top_role:  # Check if the user has a higher role
            await ctx.response.send_message('You cannot kick a user with a higher or equal role.', ephemeral=True)
            return

        # Check if the bot has the permissions to kick members
        if not ctx.guild.me.top_role.permissions.kick_members:
            await ctx.response.send_message('I do not have the permissions to kick members.', ephemeral=True)
            return

        # Check if the user who's kicking has permissions
        if not ctx.user.guild_permissions.kick_members:
            await ctx.response.send_message("You do not have permissions to kick members.", ephemeral=True)
            return

        if send_dm and user.can_send():
            await user.send(f'You have been kicked from {ctx.guild.name} for {reason} by {ctx.user.display_name}.')

        await user.kick(user, reason=reason)
        await ctx.response.send_message(f'Successfully kicked {user.mention} for {reason}.', ephemeral=True)

    @discord.slash_command(name='ban', description='Ban a user from the server')
    @commands_ext.guild_only()
    @commands_ext.has_permissions(ban_members=True)
    @discord.option(name='user', description='The user to ban', type=discord.Member)
    @discord.option(name='reason', description='The reason for banning', type=str)
    @discord.option(name='send_dm', description='Send a DM to the user', type=bool)
    @is_blocked()
    @analytics("ban")
    async def ban_user(self, ctx: discord.ApplicationContext, user: discord.Member, reason: str, send_dm: bool = True):

        if user.id == self.bot.user.id:  # Check if the user is the bot
            await ctx.response.send_message('I cannot ban myself.', ephemeral=True)
            return

        if user.id == ctx.user.id:  # Check if the user is the author
            await ctx.response.send_message('You cannot ban yourself.', ephemeral=True)
            return

        if user.top_role >= ctx.user.top_role:  # Check if the user has a higher role
            await ctx.response.send_message('You cannot ban a user with a higher or equal role.', ephemeral=True)
            return

        # Check if the bot has the permissions to ban members
        if not ctx.guild.me.top_role.permissions.ban_members:
            await ctx.response.send_message('I do not have the permissions to ban members.', ephemeral=True)
            return

        # Check if the user who's ban has permissions
        if not ctx.user.guild_permissions.ban_members:
            await ctx.response.send_message("You do not have permissions to ban members.", ephemeral=True)
            return

        if send_dm and user.can_send():
            await user.send(f'You have been banned from {ctx.guild.name} for {reason} by {ctx.user.display_name}.')

        await user.ban(user, reason=reason)
        await ctx.response.send_message(f'Successfully banned {user.mention} for {reason}.', ephemeral=True)

    @discord.slash_command(name='timeout', description='Time out a user from the server')
    @commands_ext.guild_only()
    @commands_ext.has_permissions(mute_members=True)
    @discord.option(name='user', description='The user to time out', type=discord.Member)
    @discord.option(name='reason', description='The reason for timing out', type=str)
    @discord.option(name='send_dm', description='Send a DM to the user', type=bool)
    @discord.option(name='days', description='The number of days to time out', type=int)
    @discord.option(name='hours', description='The number of hours to time out', type=int)
    @discord.option(name='minutes', description='The number of minutes to time out', type=int)
    @is_blocked()
    @analytics("timeout")
    async def timeout_user(self, ctx: discord.ApplicationContext, user: discord.Member, reason: str, days: int,
                           send_dm: bool = True, hours: int = 0, minutes: int = 0):

        if user.id == self.bot.user.id:  # Check if the user is the bot
            await ctx.response.send_message('I cannot time out myself.', ephemeral=True)
            return

        if user.id == ctx.user.id:  # Check if the user is the author
            await ctx.response.send_message('You cannot time out yourself.', ephemeral=True)
            return

        if user.top_role >= ctx.user.top_role:  # Check if the user has a higher role
            await ctx.response.send_message('You cannot time out a user with a higher or equal role.', ephemeral=True)
            return

        # Check if the bot has the permissions to mute members
        if not ctx.guild.me.top_role.permissions.mute_members:
            await ctx.response.send_message('I do not have the permissions to time out members.', ephemeral=True)
            return

        # Check if the user who's timing out has permissions
        if not ctx.user.guild_permissions.mute_members:
            await ctx.response.send_message("You do not have permissions to timeout members.", ephemeral=True)
            return

        total_seconds = days * 86400 + hours * 3600 + minutes * 60
        if total_seconds > 2419200:
            await ctx.response.send_message('The maximum timeout duration is 28 days.',
                                            ephemeral=True)
            return

        if send_dm and user.can_send():
            await user.send(
                f'You have been timed out from {ctx.guild.name} for {reason} by {ctx.user.display_name} for {pretty_time_delta(total_seconds)}.')

        await user.timeout_for(datetime.timedelta(seconds=total_seconds), reason=reason)
        await ctx.response.send_message(
            f'Successfully banned {user.mention} for {reason} for {pretty_time_delta(total_seconds)}.', ephemeral=True)

    @discord.slash_command(name='remove_timeout', description='Remove a timeout from a user on the server')
    @commands_ext.guild_only()
    @commands_ext.has_permissions(ban_members=True)
    @discord.option(name='user', description='The user to remove the timeout from', type=discord.Member)
    @discord.option(name='reason', description='The reason for removing', type=str)
    @discord.option(name='send_dm', description='Send a DM to the user', type=bool)
    @is_blocked()
    @analytics("remove_timeout")
    async def remove_timeout_user(self, ctx: discord.ApplicationContext, user: discord.Member, reason: str,
                                  send_dm: bool = True):

        if user.id == self.bot.user.id:  # Check if the user is the bot
            await ctx.response.send_message('I cannot ban myself.', ephemeral=True)
            return

        if user.id == ctx.user.id:  # Check if the user is the author
            await ctx.response.send_message('You cannot ban yourself.', ephemeral=True)
            return

        if user.top_role >= ctx.user.top_role:  # Check if the user has a higher role
            await ctx.response.send_message('You cannot ban a user with a higher or equal role.', ephemeral=True)
            return

        # Check if the bot has the permissions to time out members
        if not ctx.guild.me.top_role.permissions.mute_members:
            await ctx.response.send_message('I do not have the permissions to ban members.', ephemeral=True)
            return

        # Check if the user who's timing out has permissions
        if not ctx.user.guild_permissions.mute_members:
            await ctx.response.send_message("You do not have permissions to kick members.", ephemeral=True)
            return

        if send_dm and user.can_send():
            await user.send(
                f'Your timeout in {ctx.guild.name} has been removed for {reason} by {ctx.user.display_name}.')

        await user.remove_timeout(user, reason=reason)
        await ctx.response.send_message(f'Successfully banned {user.mention} for {reason}.', ephemeral=True)
