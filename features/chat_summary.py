import datetime

import discord
import sentry_sdk
from discord.ext import commands as commands_ext
from discord.ext import tasks

from database import get_conn
from utils.analytics import analytics
from utils.languages import get_translation_for_key_localized as trl
from utils.logging_util import log_into_logs
from utils.settings import get_setting, set_setting
from utils.tzutil import get_now_for_server


class ChatSummary(discord.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        super().__init__()
        self.bot = bot

        async def init_async():
            db = await get_conn()
            await db.execute("PRAGMA table_info(chat_summary)")
            # Check if the format is correct, there should be 4 columns of info, if not, delete and recreate table.

            # Set up new tables
            await db.execute('CREATE TABLE IF NOT EXISTS chat_summary(guild_id INTEGER, channel_id INTEGER, enabled INTEGER, messages INTEGER)')
            await db.execute('CREATE INDEX IF NOT EXISTS chat_summary_i ON chat_summary(guild_id, channel_id)')

            # Create the rest of tables
            await db.execute('CREATE TABLE IF NOT EXISTS chat_summary_members(guild_id INTEGER, channel_id INTEGER, member_id INTEGER, messages INTEGER)')
            await db.execute('CREATE INDEX IF NOT EXISTS chat_summary_members_i ON chat_summary_members(guild_id, channel_id, member_id)')

            # Save
            await db.commit()
            await db.close()

        self.bot.loop.create_task(init_async())

    @discord.Cog.listener()
    async def on_ready(self):
        self.summarize.start()

    @discord.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild is None:
            return

        if message.author.bot:
            return

        db = await get_conn()
        cur = await db.execute('SELECT * FROM chat_summary WHERE guild_id = ? AND channel_id = ?', (message.guild.id, message.channel.id))
        if not await cur.fetchone():
            await db.execute('INSERT INTO chat_summary(guild_id, channel_id, enabled, messages) VALUES (?, ?, ?, ?)', (message.guild.id, message.channel.id, 0, 0))

        # Increment total message count
        await db.execute('UPDATE chat_summary SET messages = messages + 1 WHERE guild_id = ? AND channel_id = ?', (message.guild.id, message.channel.id))

        # Increment message count for specific member
        cur = await db.execute('SELECT * FROM chat_summary_members WHERE guild_id = ? AND channel_id = ? AND member_id = ?', (message.guild.id, message.channel.id, message.author.id))
        if not await cur.fetchone():
            await db.execute('INSERT INTO chat_summary_members(guild_id, channel_id, member_id, messages) VALUES (?, ?, ?, ?)', (message.guild.id, message.channel.id, message.author.id, 0))

        await db.execute('UPDATE chat_summary_members SET messages = messages + 1 WHERE guild_id = ? AND channel_id = ? AND member_id = ?', (message.guild.id, message.channel.id, message.author.id))

        await db.commit()
        await db.close()

    @discord.Cog.listener()
    async def on_message_edit(self, old_message: discord.Message, new_message: discord.Message):
        if new_message.guild is None:
            return

        if new_message.author.bot:
            return

        countedits = await get_setting(new_message.guild.id, "chatsummary_countedits", "False")
        if countedits == "False":
            return

        db = await get_conn()
        cur = await db.execute('SELECT * FROM chat_summary WHERE guild_id = ? AND channel_id = ?', (old_message.guild.id, old_message.channel.id))
        if not await cur.fetchone():
            await db.execute('INSERT INTO chat_summary(guild_id, channel_id, enabled, messages) VALUES (?, ?, ?, ?)', (old_message.guild.id, old_message.channel.id, 0, 0))

        # Increment total old_message count
        await db.execute('UPDATE chat_summary SET messages = messages + 1 WHERE guild_id = ? AND channel_id = ?', (old_message.guild.id, old_message.channel.id))

        # Increment old_message count for specific member
        cur = await db.execute('SELECT * FROM chat_summary_members WHERE guild_id = ? AND channel_id = ? AND member_id = ?', (old_message.guild.id, old_message.channel.id, old_message.author.id))
        if not await cur.fetchone():
            await db.execute('INSERT INTO chat_summary_members(guild_id, channel_id, member_id, messages) VALUES (?, ?, ?, ?)',
                (old_message.guild.id, old_message.channel.id, old_message.author.id, 0))

        await db.execute('UPDATE chat_summary_members SET messages = messages + 1 WHERE guild_id = ? AND channel_id = ? AND member_id = ?',
            (old_message.guild.id, old_message.channel.id, old_message.author.id))

        await db.commit()
        await db.close()

    @tasks.loop(minutes=1)
    async def summarize(self):
        db = await get_conn()
        try:
            cur = await db.execute('SELECT guild_id, channel_id, messages FROM chat_summary WHERE enabled = 1')
            for i in await cur.fetchall():
                yesterday = await get_now_for_server(i[0])

                if yesterday.hour != 0 or yesterday.minute != 0:
                    continue

                guild = self.bot.get_guild(i[0])
                if guild is None:
                    continue

                channel = guild.get_channel(i[1])
                if channel is None:
                    continue

                if not channel.can_send():
                    continue

                yesterday = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)  # Get yesterday

                # Get date format
                date_format = await get_setting(guild.id, "chatsummary_dateformat", "YYYY/MM/DD")

                # Better formatting for day
                day = str(yesterday.day)
                if len(day) == 1:
                    day = "0" + day

                # Better formatting for the month
                month = str(yesterday.month)
                if len(month) == 1:
                    month = "0" + month

                # Select appropriate date format
                if date_format == "DD/MM/YYYY":
                    date = f"{day}/{month}/{yesterday.year}"
                elif date_format == "DD. MM. YYYY":
                    date = f"{day}. {month}. {yesterday.year}"
                elif date_format == "YYYY/DD/MM":
                    date = f"{yesterday.year}/{day}/{month}"
                elif date_format == "MM/DD/YYYY":
                    date = f"{month}/{day}/{yesterday.year}"
                elif date_format == "YYYY年MM月DD日":
                    date = f"{yesterday.year}年{month}月{day}日"
                else:
                    date = f"{yesterday.year}/{month}/{day}"

                chat_summary_message = (await trl(0, guild.id, "chat_summary_title")).format(date=date)
                chat_summary_message += '\n'
                chat_summary_message += (await trl(0, guild.id, "chat_summary_messages")).format(messages=i[2])

                await db.execute('SELECT member_id, messages FROM chat_summary_members WHERE guild_id = ? AND channel_id = ? ORDER BY '
                                 'messages DESC LIMIT 5', (i[0], i[1]))

                jndex = 0  # idk
                for j in cur.fetchall():
                    jndex += 1
                    member = guild.get_member(j[0])
                    if member is not None:
                        chat_summary_message += (await trl(0, guild.id, "chat_summary_line")).format(position=jndex, name=member.display_name, messages=j[1])
                    else:
                        chat_summary_message += (await trl(0, guild.id, "chat_summary_line_unknown_user")).format(position=jndex, id=j[0], messages=j[1])

                try:
                    await channel.send(chat_summary_message)
                except Exception as e:
                    sentry_sdk.capture_exception(e)

                await db.execute('UPDATE chat_summary SET messages = 0 WHERE guild_id = ? AND channel_id = ?', (i[0], i[1]))
                await db.execute('DELETE FROM chat_summary_members WHERE guild_id = ? AND channel_id = ?', (i[0], i[1]))
        finally:
            await db.commit()
            await db.close()

    chat_summary_subcommand = discord.SlashCommandGroup(name='chatsummary', description='Chat summary')

    @chat_summary_subcommand.command(name="add", description="Add a channel to count to chat summary")
    @commands_ext.guild_only()
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.bot_has_permissions(send_messages=True)
    @analytics("chatsummary add")
    async def command_add(self, ctx: discord.ApplicationContext, channel: discord.TextChannel):
        db = await get_conn()

        # Add channel to chat summary if not already there
        cur = await db.execute('SELECT * FROM chat_summary WHERE guild_id = ? AND channel_id = ?', (ctx.guild.id, channel.id))
        if not await cur.fetchone():
            await db.execute('INSERT INTO chat_summary(guild_id, channel_id, enabled, messages) VALUES (?, ?, ?, ?)', (ctx.guild.id, channel.id, 0, 0))

        # Check enabled state
        cur = await db.execute('SELECT enabled FROM chat_summary WHERE guild_id = ? AND channel_id = ?', (ctx.guild.id, channel.id))
        data = await cur.fetchone()
        if data is not None and data[0] == 1:
            await ctx.respond(await trl(ctx.user.id, ctx.guild.id, "chat_summary_add_already_added"), ephemeral=True)
            return

        # Enable
        await db.execute('UPDATE chat_summary SET enabled = 1 WHERE guild_id = ? AND channel_id = ?', (ctx.guild.id, channel.id))
        await db.commit()
        await db.close()

        # Logging embed
        logging_embed = discord.Embed(title=await trl(0, ctx.guild.id, "chat_summary_add_log_title"))
        logging_embed.add_field(name=await trl(0, ctx.guild.id, "logging_channel"), value=f"{channel.mention}")
        logging_embed.add_field(name=await trl(0, ctx.guild.id, "logging_user"), value=f"{ctx.user.mention}")

        # Log into logs
        await log_into_logs(ctx.guild, logging_embed)

        # Send response
        await ctx.respond(await trl(ctx.user.id, ctx.guild.id, "chat_summary_add_added", append_tip=True), ephemeral=True)

    @chat_summary_subcommand.command(name="remove", description="Remove a channel from being counted to chat summary")
    @commands_ext.guild_only()
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @analytics("chatsummary remove")
    async def command_remove(self, ctx: discord.ApplicationContext, channel: discord.TextChannel):
        db = await get_conn()

        # Check if present into database
        cur = await db.execute('SELECT * FROM chat_summary WHERE guild_id = ? AND channel_id = ?', (ctx.guild.id, channel.id))
        if not await cur.fetchone():
            await db.execute('INSERT INTO chat_summary(guild_id, channel_id, enabled, messages) VALUES (?, ?, ?, '
                             '?)', (ctx.guild.id, channel.id, 0, 0))

        # Check enabled
        cur = await db.execute('SELECT enabled FROM chat_summary WHERE guild_id = ? AND channel_id = ?', (ctx.guild.id, channel.id))
        data = await cur.fetchone()
        if data is not None and data[0] == 0:
            await ctx.respond(await trl(ctx.user.id, ctx.guild.id, "chat_summary_remove_already_removed"), ephemeral=True)
            return

        # Set disabled
        await db.execute('UPDATE chat_summary SET enabled = 0 WHERE guild_id = ? AND channel_id = ?', (ctx.guild.id, channel.id))
        await db.commit()
        await db.close()

        # Logging embed
        logging_embed = discord.Embed(title=await trl(ctx.user.id, ctx.guild.id, "chat_summary_remove_log_title"))
        logging_embed.add_field(name=await trl(ctx.user.id, ctx.guild.id, "logging_channel"), value=f"{channel.mention}")
        logging_embed.add_field(name=await trl(ctx.user.id, ctx.guild.id, "logging_user"), value=f"{ctx.user.mention}")

        # Send
        await log_into_logs(ctx.guild, logging_embed)

        # Respond
        await ctx.respond(await trl(ctx.user.id, ctx.guild.id, "chat_summary_remove_removed", append_tip=True), ephemeral=True)

    @chat_summary_subcommand.command(name="dateformat", description="Set the date format of Chat Streak messages.")
    @commands_ext.guild_only()
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @discord.option(name="date_format", description="Format", choices=["YYYY/MM/DD", "DD/MM/YYYY", "DD. MM. YYYY", "YYYY/DD/MM", "MM/DD/YYYY", "YYYY年MM月DD日"])
    @analytics("chatsummary dateformat")
    async def summary_dateformat(self, ctx: discord.ApplicationContext, date_format: str):
        # Get old setting
        old_date_format = await get_setting(ctx.guild.id, "chatsummary_dateformat", "YYYY/MM/DD")

        # Save setting
        await set_setting(ctx.guild.id, "chatsummary_dateformat", date_format)

        # Create logging embed
        logging_embed = discord.Embed(title=await trl(0, ctx.guild.id, "chat_summary_dateformat_log_title"))
        logging_embed.add_field(name=await trl(0, ctx.guild.id, "chat_summary_dateformat_log_dateformat"), value=f"{old_date_format} -> {date_format}")
        logging_embed.add_field(name=await trl(0, ctx.guild.id, "logging_user"), value=f"{ctx.user.mention}")

        # Send
        await log_into_logs(ctx.guild, logging_embed)

        # Respond
        await ctx.respond((await trl(ctx.user.id, ctx.guild.id, "chat_summary_dateformat_set", append_tip=True)).format(format=date_format), ephemeral=True)

    @chat_summary_subcommand.command(name="countedits", description="Enable or disable counting of message edits as sent messages.")
    @commands_ext.guild_only()
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @analytics("chatsummary countedits")
    async def chatsummary_countedits(self, ctx: discord.ApplicationContext, countedits: bool):
        # Get old setting
        old_count_edits = await get_setting(ctx.guild.id, "chatsummary_count_edits", str(False))

        # Save setting
        await set_setting(ctx.guild.id, "chatsummary_countedits", str(countedits))

        # Create logging embed
        logging_embed = discord.Embed(title=await trl(0, ctx.guild.id, "chat_summary_count_edits_log_title"))
        logging_embed.add_field(name=await trl(0, ctx.guild.id, "chat_summary_count_edits_log_count_edits"),
                                value="{old} -> {new}".format(old=("Yes" if old_count_edits == "True" else "No"), new=("Yes" if countedits else "No")))
        logging_embed.add_field(name=await trl(0, ctx.guild.id, "logging_user"), value=f"{ctx.user.mention}")

        # Send
        await log_into_logs(ctx.guild, logging_embed)

        # Respond
        await ctx.respond(await trl(ctx.user.id, ctx.guild.id, "chat_summary_count_edits_on", append_tip=True) if countedits else await trl(ctx.user.id, ctx.guild.id, "chat_summary_count_edits_off",
                                                                                                                                            append_tip=True), ephemeral=True)
