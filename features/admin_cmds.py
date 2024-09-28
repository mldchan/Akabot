import os

import discord

from utils.announcement_channels import db_get_all_announcement_channels
from utils.config import get_key
# Let's say that trl is the short form of get_translation_for_key_localized across the codebase
from utils.languages import get_translation_for_key_localized as trl

ADMIN_GUILD = int(get_key("Admin_GuildID", "0"))
OWNER_ID = int(get_key("Admin_OwnerID", "0"))
ANNOUNCEMENT_CHANNEL = int(get_key("Admin_AnnouncementChannel", "0"))


class AdminCommands(discord.Cog):

    def __init__(self, bot: discord.Bot):
        super().__init__()
        self.bot = bot

    admin_subcommand = discord.SlashCommandGroup(name="admin", description="Manage the bot", guild_ids=[ADMIN_GUILD])

    @admin_subcommand.command(name="server_count", description="How many servers is the bot in?")
    async def admin_servercount(self, ctx: discord.ApplicationContext):
        servers = len(self.bot.guilds)
        channels = len([channel for channel in self.bot.get_all_channels()])
        members = len(set([member for member in self.bot.get_all_members()]))

        await ctx.respond(
            (await trl(ctx.user.id, ctx.guild.id, "bot_status_message")).format(servers=str(servers), channels=str(channels),
                                                                        users=str(members)), ephemeral=True)

    @admin_subcommand.command(name="create_announcement", description="List all announcement channels")
    async def create_announcement(self, ctx: discord.ApplicationContext, announcement_file: discord.Attachment,
                                  extra_attachment: discord.Attachment = None):
        await ctx.defer()

        if ANNOUNCEMENT_CHANNEL == 0:
            await ctx.respond(content=await trl(ctx.user.id, ctx.guild.id, "announcement_not_set"), ephemeral=True)
            return

        if not announcement_file.filename.endswith(".md"):
            await ctx.respond(await trl(ctx.user.id, ctx.guild.id, "announcement_file_not_md"), ephemeral=True)
            return

        await announcement_file.save("temp.md")
        await extra_attachment.save(extra_attachment.filename)

        with open("temp.md", "r") as f:
            announcement = f.read()

        if len(announcement) > 2000:
            await ctx.respond(await trl(ctx.user.id, ctx.guild.id, "announcement_too_long"), ephemeral=True)
            return

        msg: discord.Message | None = await ctx.followup.send(content="Creating announcement...")
        if msg is None:
            return

        first_channel = self.bot.get_channel(ANNOUNCEMENT_CHANNEL)
        if not first_channel:
            await ctx.respond(await trl(ctx.user.id, ctx.guild.id, "announcement_channel_not_found"), ephemeral=True)
            return

        await first_channel.send(announcement, file=discord.File(extra_attachment.filename))

        await msg.edit(content=await trl(ctx.user.id, ctx.guild.id, "announcement_sent_sending_to_subscribed"))
        channels = await db_get_all_announcement_channels()
        i = 0
        for channel in channels:
            i += 1

            if i % 10 == 0:
                await msg.edit(
                    content=(await trl(ctx.user.id, ctx.guild.id, "announcement_sent_sending_to_subscribed_progress")).format(
                        progress=str(i), count=str(len(channels))))

            try:
                channel = self.bot.get_channel(channel[1])
                if not channel:
                    continue

                await channel.send(announcement, file=discord.File(extra_attachment.filename))
            except discord.Forbidden:
                continue

        await msg.edit(content=await trl(ctx.user.id, ctx.guild.id, "announcement_sent"))

        os.remove("temp.md")
        os.remove(extra_attachment.filename)
