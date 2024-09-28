import discord

from utils.announcement_channels import db_init, db_get_announcement_channels, db_remove_announcement_channel, \
    db_add_announcement_channel, db_is_subscribed_to_announcements
from utils.languages import get_translation_for_key_localized as trl, get_language
from utils.per_user_settings import get_per_user_setting
from utils.tips import append_tip_to_message


class AnnouncementChannels(discord.Cog):
    def __init__(self, bot: discord.Bot):
        bot.loop.create_task(db_init())
        self.bot = bot

    announcement_channels_group = discord.SlashCommandGroup(name="announcement_channels",
                                                            description="Subscribe to Akabot announcements")

    @announcement_channels_group.command(name="subscribe",
                                         description="Subscribe a channel to Akabot announcements")
    async def announcement_channels_subscribe(self, ctx: discord.ApplicationContext, channel: discord.TextChannel):
        if not channel.permissions_for(ctx.guild.me).send_messages:
            await ctx.respond(await trl(ctx.author.id, ctx.guild.id, "announcement_no_send_messages_permission"),
                              ephemeral=True)
            return

        db_add_announcement_channel(ctx.guild.id, channel.id)
        await ctx.respond(
            await trl(ctx.user.id, ctx.guild.id, "announcement_subscribed", append_tip=True).format(channel=channel.mention),
            ephemeral=True)

    @announcement_channels_group.command(name="unsubscribe",
                                         description="Unsubscribe a channel from Akabot announcements")
    async def announcement_channels_unsubscribe(self, ctx: discord.ApplicationContext, channel: discord.TextChannel):
        if not db_is_subscribed_to_announcements(ctx.guild.id, channel.id):
            await ctx.respond(
                await trl(ctx.author.id, ctx.guild.id, "announcement_not_subscribed").format(channel=channel.mention),
                ephemeral=True)
            return

        db_remove_announcement_channel(ctx.guild.id, channel.id)
        await ctx.respond(await trl(ctx.author.id, ctx.guild.id, "announcement_unsubscribed", append_tip=True).format(
            channel=channel.mention),
            ephemeral=True)

    @announcement_channels_group.command(name="list",
                                         description="List all channels subscribed to Akabot announcements")
    async def announcement_channels_list(self, ctx: discord.ApplicationContext):
        channels = db_get_announcement_channels(ctx.guild.id)
        if not channels:
            await ctx.respond(await trl(ctx.author.id, ctx.guild.id, "announcement_none_subscribed"),
                              ephemeral=True)
            return

        channel_mentions = [f"<#{channel[1]}>" for channel in channels]
        message = "\n".join(channel_mentions)
        if get_per_user_setting(ctx.user.id, "tips_enabled", "true") == "true":
            language = await get_language(ctx.guild.id, ctx.user.id)
            message = append_tip_to_message(ctx.guild.id, ctx.user.id, message, language)
        await ctx.respond(message, ephemeral=True)
