import time

import discord
from discord.ext import commands as commands_ext

from utils.analytics import analytics
from utils.blocked import is_blocked
from utils.settings import get_setting, set_setting
from utils.logging import log_into_logs

class ViolationCounters:
    past_actions = []

    def add_action(self, action: str, user: discord.Member, expires: int):
        if expires < 0:
            raise ValueError('expires must be greater than 0')

        self.past_actions.append({'action': action, 'user': user, 'expires': expires + time.time()})

    def filter_expired_actions(self):
        self.past_actions = [action for action in self.past_actions if action['expires'] > time.time()]

    def count_actions(self, action: str, user: discord.Member):
        self.filter_expired_actions()
        return len([a for a in self.past_actions if a['action'] == action and a['user'] == user])


class AntiRaid(discord.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        super().__init__()
        self.bot = bot
        self.violation_counters = ViolationCounters()

    @discord.Cog.listener()
    @is_blocked()
    async def on_member_join(self, member: discord.Member):
        self.violation_counters.filter_expired_actions()

        antiraid_join_threshold = get_setting(member.guild.id, "antiraid_join_threshold", "5")
        antiraid_join_threshold_per = get_setting(member.guild.id, "antiraid_join_threshold_per", "60")

        if self.violation_counters.count_actions('join', member) > int(antiraid_join_threshold):
            if not member.guild.me.guild_permissions.kick_members:
                return  # TODO: Send a warning if possible

            if member.can_send():
                await member.send(
                    content="You have been kicked from the server for suspected raiding. If you believe this was a mistake, try rejoining in a few minutes.")
            await member.kick(reason='Suspected raiding')
            return

        self.violation_counters.add_action('join', member, int(antiraid_join_threshold_per))

    antiraid_subcommand = discord.SlashCommandGroup(name='antiraid', description='Manage the antiraid settings')

    @antiraid_subcommand.command(name="join_threshold", description="Set the join threshold for the antiraid system")
    @discord.default_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @discord.option(name='people', description='The number of people joining...', type=int)
    @discord.option(name='per', description='...per the number of seconds to check', type=int)
    @is_blocked()
    @analytics("antiraid join threshold")
    async def set_join_threshold(self, ctx: discord.ApplicationContext, people: int, per: int):
        # Get old settings
        old_join_threshold = get_setting(ctx.guild.id, "antiraid_join_threshold", "5")
        old_join_threshold_per = get_setting(ctx.guild.id, "antiraid_join_threshold_per", "60")

        # Set new settings
        set_setting(ctx.guild.id, 'antiraid_join_threshold', str(people))
        set_setting(ctx.guild.id, 'antiraid_join_threshold_per', str(per))

        # Create logging embed
        logging_embed = discord.Embed(title="Antiraid Join Threshold was changed")
        logging_embed.add_field(name="Join Threshold", value=f"{str(old_join_threshold)} -> {str(people)}", inline=True)
        logging_embed.add_field(name="Per", value=f"{str(old_join_threshold_per)} -> {str(per)}", inline=True)
        logging_embed.add_field(name="User", value=f"{ctx.user.mention}", inline=False)

        # Send log into logs
        await log_into_logs(ctx.guild, logging_embed)

        # Send response to user
        await ctx.respond(f'Successfully set the join threshold to {people} per {per} seconds.', ephemeral=True)

    @antiraid_subcommand.command(name="list", description="List the antiraid settings")
    @discord.default_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @is_blocked()
    @analytics("antiraid list")
    async def list_settings(self, ctx: discord.ApplicationContext):
        join_threshold = get_setting(ctx.guild.id, 'antiraid_join_threshold', 5)
        join_threshold_per = get_setting(ctx.guild.id, 'antiraid_join_threshold_per', 60)

        embed = discord.Embed(title='Antiraid settings', color=discord.Color.blurple())
        embed.add_field(name='Join threshold', value=f'{join_threshold} per {join_threshold_per} seconds')

        await ctx.respond(embed=embed, ephemeral=True)
