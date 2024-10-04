import discord
from discord.ext import commands

from database import client
from utils.languages import get_translation_for_key_localized as trl
from utils.settings import get_setting, set_setting


class Suggestions(discord.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @discord.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if client['SuggestionChannels'].count_documents({'ChannelID': message.guild.id}) != 0:
            emojis = get_setting(message.guild.id, 'suggestion_emoji', '👍👎')
            if emojis == '👍👎':
                await message.add_reaction('👍')
                await message.add_reaction('👎')
            elif emojis == '✅❌':
                await message.add_reaction('✅')
                await message.add_reaction('❌')

            if get_setting(message.guild.id, "suggestion_reminder_enabled", "false") == "true":
                to_send = get_setting(message.guild.id, "suggestion_reminder_message", "")
                sent = await message.reply(to_send)
                await sent.delete(delay=5)

    suggestions_group = discord.SlashCommandGroup(name='suggestions', description='Suggestion commands')

    @suggestions_group.command(name='add_channel', description='Add a suggestion channel')
    @discord.default_permissions(manage_guild=True)
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def cmd_add_channel(self, ctx: discord.ApplicationContext, channel: discord.TextChannel):
        if client['SuggestionChannels'].count_documents({'ChannelID': ctx.guild.id}) == 0:
            client['SuggestionChannels'].insert_one({'GuildID': ctx.guild.id, 'ChannelID': channel.id})
            await ctx.respond(trl(ctx.user.id, ctx.guild.id, 'suggestions_channel_added', append_tip=True).format(channel=channel.mention), ephemeral=True)
        else:
            await ctx.respond(trl(ctx.user.id, ctx.guild.id, 'suggestions_channel_already_exists'), ephemeral=True)

    @suggestions_group.command(name='remove_channel', description='Remove a suggestion channel')
    @discord.default_permissions(manage_guild=True)
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def cmd_remove_channel(self, ctx: discord.ApplicationContext, channel: discord.TextChannel):
        if client['SuggestionChannels'].count_documents({'ChannelID': ctx.guild.id}) == 0:
            await ctx.respond(trl(ctx.user.id, ctx.guild.id, "suggestions_channel_not_found"), ephemeral=True)
        else:
            client['SuggestionChannels'].delete_one({'ChannelID': ctx.guild.id})
            await ctx.respond(trl(ctx.user.id, ctx.guild.id, "suggestions_channel_removed", append_tip=True).format(channel=channel.mention), ephemeral=True)

    @suggestions_group.command(name='emoji', description='Choose emoji')
    @discord.default_permissions(manage_guild=True)
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    @discord.option(name='emoji', description='The emoji to use', choices=['👎👍', '✅❌'])
    async def cmd_choose_emoji(self, ctx: discord.ApplicationContext, emoji: str):
        set_setting(ctx.guild.id, 'suggestion_emoji', emoji)
        await ctx.respond(trl(ctx.user.id, ctx.guild.id, "suggestions_emoji_set").format(emoji=emoji), ephemeral=True)

    @suggestions_group.command(name='message_reminder', description="Message reminder for people posting suggestions")
    @discord.default_permissions(manage_guild=True)
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def cmd_message_reminder(self, ctx: discord.ApplicationContext, enabled: bool, message: str):
        if len(message) < 1:
            await ctx.respond("Invalid message input.", ephemeral=True)
        set_setting(ctx.guild.id, 'suggestion_reminder_enabled', str(enabled).lower())
        set_setting(ctx.guild.id, 'suggestion_reminder_message', message)
        await ctx.respond(trl(ctx.user.id, ctx.guild.id, 'suggestions_message_reminder_set', append_tip=True).format(enabled=enabled, message=message), ephemeral=True)
