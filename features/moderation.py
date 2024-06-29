import datetime

import discord
from discord.ext import commands as commands_ext

from utils.analytics import analytics
from utils.blocked import is_blocked
from utils.settings import get_setting, set_setting

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

    moderation_subcommand = discord.SlashCommandGroup(name='moderation', description='Moderation commands')

    @discord.slash_command(name='kick', description='Kick a user from the server')
    @commands_ext.guild_only()
    @discord.default_permissions(kick_members=True)
    @commands_ext.has_permissions(kick_members=True)
    @commands_ext.bot_has_permissions(kick_members=True)
    @discord.option(name='user', description='The user to kick', type=discord.Member)
    @discord.option(name='reason', description='The reason for kicking', type=str)
    @discord.option(name='send_dm', description='Send a DM to the user', type=bool, required=False, default=True)
    @is_blocked()
    @analytics("kick")
    async def kick_user(self, ctx: discord.ApplicationContext, user: discord.Member, reason: str, send_dm: bool = True):

        if user.id == self.bot.user.id:  # Check if the user is the bot
            await ctx.respond('I cannot kick myself.', ephemeral=True)
            return

        if user.id == ctx.user.id:  # Check if the user is the author
            await ctx.respond('You cannot kick yourself.', ephemeral=True)
            return

        if user.top_role >= ctx.user.top_role:  # Check if the user has a higher role
            await ctx.respond('You cannot kick a user with a higher or equal role.', ephemeral=True)
            return

        if send_dm and user.can_send():
            try:
                await user.send(f'You have been kicked from {ctx.guild.name} for {reason} by {ctx.user.display_name}.')
            except discord.Forbidden:
                pass

        await user.kick(reason=reason)

        ephemerality = get_setting(ctx.guild.id, "moderation_ephemeral", "true")
        await ctx.respond(f'Successfully kicked {user.mention} for {reason}.', ephemeral=ephemerality == "true")

    @discord.slash_command(name='ban', description='Ban a user from the server')
    @commands_ext.guild_only()
    @discord.default_permissions(ban_members=True)
    @commands_ext.has_permissions(ban_members=True)
    @commands_ext.bot_has_permissions(ban_members=True)
    @discord.option(name='user', description='The user to ban', type=discord.Member)
    @discord.option(name='reason', description='The reason for banning', type=str)
    @discord.option(name='send_dm', description='Send a DM to the user', type=bool)
    @is_blocked()
    @analytics("ban")
    async def ban_user(self, ctx: discord.ApplicationContext, user: discord.Member, reason: str, send_dm: bool = True):

        if user.id == self.bot.user.id:  # Check if the user is the bot
            await ctx.respond('I cannot ban myself.', ephemeral=True)
            return

        if user.id == ctx.user.id:  # Check if the user is the author
            await ctx.respond('You cannot ban yourself.', ephemeral=True)
            return

        if user.top_role >= ctx.user.top_role:  # Check if the user has a higher role
            await ctx.respond('You cannot ban a user with a higher or equal role.', ephemeral=True)
            return

        if send_dm and user.can_send():
            try:
                await user.send(f'You have been banned from {ctx.guild.name} for {reason} by {ctx.user.display_name}.')
            except discord.Forbidden:
                pass

        await user.ban(reason=reason)

        ephemerality = get_setting(ctx.guild.id, "moderation_ephemeral", "true")
        await ctx.respond(f'Successfully banned {user.mention} for {reason}.', ephemeral=ephemerality == "true")

    @discord.slash_command(name='timeout', description='Time out a user from the server. If a user has a timeout, this will change the timeout.')
    @commands_ext.guild_only()
    @discord.default_permissions(mute_members=True)
    @commands_ext.has_permissions(mute_members=True)
    @commands_ext.bot_has_permissions(mute_members=True)
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
            await ctx.respond('I cannot time out myself.', ephemeral=True)
            return

        if user.id == ctx.user.id:  # Check if the user is the author
            await ctx.respond('You cannot time out yourself.', ephemeral=True)
            return

        if user.top_role >= ctx.user.top_role:  # Check if the user has a higher role
            await ctx.respond('You cannot time out a user with a higher or equal role.', ephemeral=True)
            return

        total_seconds = days * 86400 + hours * 3600 + minutes * 60
        if total_seconds > 2419200:
            await ctx.respond('The maximum timeout duration is 28 days.',
                                            ephemeral=True)
            return
        
        dm_has_updated = False

        if user.timed_out:
            await user.remove_timeout(reason=f"Changing of duration of timeout for: {reason}")
            dm_has_updated = True

        if send_dm and user.can_send():
            if dm_has_updated:
                try:
                    await user.send(
                f'Your timeout in {ctx.guild.name} was changed to {pretty_time_delta(total_seconds)} by {ctx.user.display_name} for {reason}.')
                except discord.Forbidden:
                    pass
            else:
                try:
                    await user.send(
                f'You have been timed out from {ctx.guild.name} for {reason} by {ctx.user.display_name} for {pretty_time_delta(total_seconds)}.')
                except discord.Forbidden:
                    pass

        await user.timeout_for(datetime.timedelta(seconds=total_seconds), reason=reason)

        ephemerality = get_setting(ctx.guild.id, "moderation_ephemeral", "true")
        await ctx.respond(
            f'Successfully timed out {user.mention} for {reason} for {pretty_time_delta(total_seconds)}.', ephemeral=ephemerality == "true")

    @discord.slash_command(name='remove_timeout', description='Remove a timeout from a user on the server')
    @commands_ext.guild_only()
    @discord.default_permissions(mute_members=True)
    @commands_ext.has_permissions(mute_members=True)
    @commands_ext.bot_has_permissions(mute_members=True)
    @discord.option(name='user', description='The user to remove the timeout from', type=discord.Member)
    @discord.option(name='reason', description='The reason for removing', type=str)
    @discord.option(name='send_dm', description='Send a DM to the user', type=bool)
    @is_blocked()
    @analytics("remove_timeout")
    async def remove_timeout_user(self, ctx: discord.ApplicationContext, user: discord.Member, reason: str,
                                  send_dm: bool = True):

        if user.id == self.bot.user.id:  # Check if the user is the bot
            await ctx.respond('I cannot ban myself.', ephemeral=True)
            return

        if user.id == ctx.user.id:  # Check if the user is the author
            await ctx.respond('You cannot ban yourself.', ephemeral=True)
            return

        if user.top_role >= ctx.user.top_role:  # Check if the user has a higher role
            await ctx.respond('You cannot timeout a user with a higher or equal role.', ephemeral=True)
            return

        if send_dm and user.can_send():
            try:
                await user.send(
                f'Your timeout in {ctx.guild.name} has been removed for {reason} by {ctx.user.display_name}.')
            except discord.Forbidden:
                pass

        await user.remove_timeout(reason=reason)

        ephemerality = get_setting(ctx.guild.id, "moderation_ephemeral", "true")
        await ctx.respond(f'Successfully unmuted {user.mention} for {reason}.', ephemeral=ephemerality == "true")

    @moderation_subcommand.command(name="ephemeral", description="Toggle the ephemeral status of a message")
    async def toggle_ephemeral(self, ctx: discord.ApplicationContext, ephemeral: bool):
        set_setting(ctx.guild.id, "moderation_ephemeral", str(ephemeral).lower())
        await ctx.respond(
            "Moderation responses are now ephemeral." if ephemeral else "Moderation responses are no longer ephemeral and will be sent publicly.",
            ephemeral=True)
