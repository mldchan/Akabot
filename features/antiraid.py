import time

import discord
from discord.ext import commands as commands_ext

from utils.analytics import analytics
from utils.languages import get_translation_for_key_localized as trl
from utils.logging_util import log_into_logs
from utils.settings import get_setting, set_setting


class ViolationCounters:
    past_actions = []

    def add_action(self, action: str, user: discord.Member, expires: int):
        if expires < 0:
            raise ValueError('expires must be greater than 0')

        # print("Appending action to past actions")
        self.past_actions.append({'action': action, 'user': user.id, 'expires': expires + time.time()})

    def filter_expired_actions(self):
        # actions_before = len(self.past_actions)
        self.past_actions = [action for action in self.past_actions if action['expires'] > time.time()]
        # print(f"Filtered {actions_before - len(self.past_actions)} expired actions")

    def count_actions(self, action: str, user: discord.Member):
        self.filter_expired_actions()
        actions = len([a for a in self.past_actions if a['action'] == action and a['user'] == user.id])
        # print(f"Counted {actions} actions")
        return actions


class AntiRaid(discord.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        super().__init__()
        self.bot = bot
        self.join_violation_counters = ViolationCounters()
        self.message_violation_counters = ViolationCounters()
        self.message_send_violation_counters = ViolationCounters()  # This one will be to avoid spamming messages

    @discord.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        self.join_violation_counters.filter_expired_actions()

        antiraid_join_threshold = await get_setting(member.guild.id, "antiraid_join_threshold", "5")
        antiraid_join_threshold_per = await get_setting(member.guild.id, "antiraid_join_threshold_per", "60")

        if self.join_violation_counters.count_actions('join', member) > int(antiraid_join_threshold):
            if not member.guild.me.guild_permissions.kick_members:
                return  # TODO: Send a warning if possible

            if member.can_send():
                await member.send(
                    content=await trl(member.id, member.guild.id, "antiraid_kicked_message"))
            await member.kick(reason=await trl(0, member.guild.id, "antiraid_kicked_audit"))
            return

        self.join_violation_counters.add_action('join', member, int(antiraid_join_threshold_per))

    antiraid_subcommand = discord.SlashCommandGroup(name='antiraid', description='Manage the antiraid settings')

    @discord.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if message.author.guild_permissions.manage_messages:
            return

        self.message_violation_counters.filter_expired_actions()

        antiraid_message_threshold = await get_setting(message.guild.id, "antiraid_message_threshold", "5")
        antiraid_message_threshold_per = await get_setting(message.guild.id, "antiraid_message_threshold_per", "5")

        if self.message_violation_counters.count_actions('message', message.author) > int(antiraid_message_threshold):
            if not message.guild.me.guild_permissions.manage_messages:
                return

            await message.delete()
            if self.message_send_violation_counters.count_actions('message_send', message.author) == 0:
                await message.channel.send((await trl(message.author.id, message.guild.id, "antiraid_dontspam_message")).format(
                    user_id=message.author.id), delete_after=5)
                self.message_send_violation_counters.add_action('message_send', message.author, 5)
            return

        self.message_violation_counters.add_action('message', message.author, int(antiraid_message_threshold_per))

    @antiraid_subcommand.command(name="join_threshold", description="Set the join threshold for the antiraid system")
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @discord.option(name='people', description='The number of people joining...', type=int)
    @discord.option(name='per', description='...per the number of seconds to check', type=int)
    @analytics("antiraid join threshold")
    async def set_join_threshold(self, ctx: discord.ApplicationContext, people: int, per: int):
        # Get old settings
        old_join_threshold = await get_setting(ctx.guild.id, "antiraid_join_threshold", "5")
        old_join_threshold_per = await get_setting(ctx.guild.id, "antiraid_join_threshold_per", "60")

        # Set new settings
        await set_setting(ctx.guild.id, 'antiraid_join_threshold', str(people))
        await set_setting(ctx.guild.id, 'antiraid_join_threshold_per', str(per))

        # Create logging embed
        logging_embed = discord.Embed(title=await trl(0, ctx.guild.id, "logging_antiraid_join_threshold_changed"))
        logging_embed.add_field(name=await trl(0, ctx.guild.id, "logging_join_threshold"),
                                value=f"{str(old_join_threshold)} -> {str(people)}", inline=True)
        logging_embed.add_field(name=await trl(0, ctx.guild.id, "logging_per"),
                                value=f"{str(old_join_threshold_per)} -> {str(per)}", inline=True)
        logging_embed.add_field(name=await trl(0, ctx.guild.id, "logging_user"),
                                value=f"{ctx.user.mention}", inline=False)

        # Send log into logs
        await log_into_logs(ctx.guild, logging_embed)

        # Send response to user
        await ctx.respond(
            (await trl(ctx.user.id, ctx.guild.id, "antiraid_join_threshold_changed", append_tip=True)).format(people=str(people), per=str(per)),
            ephemeral=True)

    @antiraid_subcommand.command(name="message_threshold",
                                 description="Set the message threshold for the antiraid system")
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @analytics("antiraid message threshold")
    async def set_message_threshold(self, ctx: discord.ApplicationContext, messages: int, per: int):
        # Get old settings
        old_message_threshold = await get_setting(ctx.guild.id, "antiraid_message_threshold", "5")
        old_message_threshold_per = await get_setting(ctx.guild.id, "antiraid_message_threshold_per", "5")

        # Set new settings
        await set_setting(ctx.guild.id, 'antiraid_message_threshold', str(messages))
        await set_setting(ctx.guild.id, 'antiraid_message_threshold_per', str(per))

        # Create logging embed
        logging_embed = discord.Embed(title=await trl(0, ctx.guild.id, "logging_antiraid_message_threshold_changed"))
        logging_embed.add_field(
            name=await trl(0, ctx.guild.id, "logging_message_threshold"),
            value=f"{str(old_message_threshold)} -> {str(messages)}", inline=True)
        logging_embed.add_field(name=await trl(0, ctx.guild.id, "logging_per"),
                                value=f"{str(old_message_threshold_per)} -> {str(per)}", inline=True)
        logging_embed.add_field(name=await trl(0, ctx.guild.id, "logging_user"),
                                value=f"{ctx.user.mention}", inline=False)

        # Send log into logs
        await log_into_logs(ctx.guild, logging_embed)

        # Send response to user
        await ctx.respond(
            (await trl(ctx.user.id, ctx.guild.id, "antiraid_message_threshold_changed", append_tip=True)).format(messages=str(messages),
                                                                                        per=str(per)),
            ephemeral=True)

    @antiraid_subcommand.command(name="list", description="List the antiraid settings")
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @analytics("antiraid list")
    async def list_settings(self, ctx: discord.ApplicationContext):
        join_threshold = await get_setting(ctx.guild.id, 'antiraid_join_threshold', '5')
        join_threshold_per = await get_setting(ctx.guild.id, 'antiraid_join_threshold_per', '60')

        embed = discord.Embed(title=await trl(ctx.user.id, ctx.guild.id, "antiraid_settings"), color=discord.Color.blurple())
        embed.add_field(name=await trl(ctx.user.id, ctx.guild.id, "logging_join_threshold"),
                        value=(await trl(ctx.user.id, ctx.guild.id, "antiraid_settings_join_threshold_value")).format(
                            joins=join_threshold, seconds=join_threshold_per), inline=True)

        await ctx.respond(embed=embed, ephemeral=True)
