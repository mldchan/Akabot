import discord
from discord.ext import commands

from database import conn
from utils.languages import get_translation_for_key_localized as trl
from utils.settings import get_setting, set_setting


class Suggestions(discord.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

        cur = conn.cursor()
        cur.execute('create table if not exists suggestion_channels(id integer primary key, channel_id text)')
        cur.close()
        conn.commit()

    @discord.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        cur = conn.cursor()
        cur.execute('select * from suggestion_channels where channel_id = ?', (message.channel.id,))
        if cur.fetchone():
            emojis = get_setting(message.guild.id, 'suggestion_emoji', '👍👎')
            if emojis == '👍👎':
                await message.add_reaction('👍')
                await message.add_reaction('👎')
            elif emojis == '✅❌':
                await message.add_reaction('✅')
                await message.add_reaction('❌')

        cur.close()
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
        cur = conn.cursor()

        cur.execute('select * from suggestion_channels where id = ?', (channel.id,))
        if cur.fetchone():
            await ctx.respond(trl(ctx.user.id, ctx.guild.id, 'suggestions_channel_already_exists'), ephemeral=True)
            cur.close()
            return

        cur.execute('insert into suggestion_channels(channel_id) values (?)', (channel.id,))
        cur.close()
        conn.commit()

        await ctx.respond(trl(ctx.user.id, ctx.guild.id, 'suggestions_channel_added', append_tip=True).format(channel=channel.mention), ephemeral=True)

    @suggestions_group.command(name='remove_channel', description='Remove a suggestion channel')
    @discord.default_permissions(manage_guild=True)
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def cmd_remove_channel(self, ctx: discord.ApplicationContext, channel: discord.TextChannel):
        cur = conn.cursor()
        cur.execute('select * from suggestion_channels where id = ?', (channel.id,))
        if not cur.fetchone():
            await ctx.respond(trl(ctx.user.id, ctx.guild.id, "suggestions_channel_not_found"), ephemeral=True)
            cur.close()
            return

        cur.execute('delete from suggestion_channels where id = ?', (channel.id,))
        cur.close()
        conn.commit()

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
        await ctx.respond(
            trl(ctx.user.id, ctx.guild.id, 'suggestions_message_reminder_set', append_tip=True).format(enabled=enabled, message=message),
            ephemeral=True)