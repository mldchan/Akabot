import datetime

import discord
import sentry_sdk
from discord.ext import tasks, commands

from database import client
from utils.analytics import analytics
from utils.languages import get_translation_for_key_localized as trl
from utils.per_user_settings import get_per_user_setting
from utils.settings import set_setting


class BirthdayAnnouncements(discord.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        super().__init__()

    birthday_announcements_group = discord.SlashCommandGroup(name="birthday_announcements",
                                                             description="Birthday Announcements commands")

    @discord.Cog.listener()
    async def on_ready(self):
        self.birthday_announcements.start()

    @tasks.loop(seconds=60)
    async def birthday_announcements(self):
        await self.handle_birthday_announcements()

    async def handle_birthday_announcements(self):
        # Check for birthdays
        now = datetime.datetime.now()
        if now.hour != 12 or now.minute != 0:
            return

        birthdays = client['UserBirthday'].find({'Birth.Year': now.year, 'Birth.Month': now.month, 'Birth.Day': now.day}).to_list()
        for birthday in birthdays:
            # Test DM
            try:
                member = self.bot.get_user(birthday['UserID'])
                if member is None:
                    continue

                if get_per_user_setting(member.id, 'birthday_send_dm', True):
                    await member.send(trl(member.id, 0, 'birthday_dm'))
            except Exception as e:
                sentry_sdk.capture_exception(e)

            # TODO: Broadcast to Discord servers

    @birthday_announcements_group.command(name="channel", description="Set the channel for birthday announcements")
    @discord.default_permissions(manage_guild=True)
    @discord.option(name="channel", description="The channel to send birthday announcements in")
    @commands.has_permissions(manage_guild=True)
    @analytics("birthday_announcements channel")
    async def set_channel(self, ctx: discord.ApplicationContext, channel: discord.TextChannel):
        set_setting(ctx.guild.id, "birthday_announcements_channel", str(channel.id))
        await ctx.respond(
            trl(ctx.user.id, ctx.guild.id, "birthday_announcements_channel_set", append_tip=True).format(channel=channel.mention),
            ephemeral=True)

    @birthday_announcements_group.command(name="message", description="Customize the birthday announcement message")
    @discord.option(name="message", description="The message to send on birthdays")
    @discord.default_permissions(manage_guild=True)
    @commands.has_permissions(manage_guild=True)
    @analytics("birthday_announcements message")
    async def birthday_announcements_message(self, ctx: discord.ApplicationContext, message: str):
        set_setting(ctx.guild.id, "birthday_announcements_message", message)
        await ctx.respond("Birthday announcement message set", ephemeral=True)
