import discord
from discord.ext import tasks, commands

from utils.analytics import analytics
from utils.languages import get_translation_for_key_localized as trl
from utils.settings import set_setting


class BirthdayAnnouncements(discord.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        super().__init__()

    birthday_announcements_group = discord.SlashCommandGroup(name="birthday_announcements",
                                                             description="Birthday Announcements commands")

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

    @discord.Cog.listener()
    async def on_ready(self):
        self.birthday_announcements.start()

    @tasks.loop(seconds=60)
    async def birthday_announcements(self):
        await self.handle_birthday_announcements()

    async def handle_birthday_announcements(self):

    # Check for birthdays


    @birthday_announcements_group.command(name="message", description="Customize the birthday announcement message")
    @discord.option(name="message", description="The message to send on birthdays")
    @discord.default_permissions(manage_guild=True)
    @commands.has_permissions(manage_guild=True)
    @analytics("birthday_announcements message")
    async def birthday_announcements_message(self, ctx: discord.ApplicationContext, message: str):
        set_setting(ctx.guild.id, "birthday_announcements_message", message)
        await ctx.respond("Birthday announcement message set", ephemeral=True)
