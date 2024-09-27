import asyncio
import datetime

import discord
from discord.ext import commands as commands_ext

from database import get_conn
from utils.analytics import analytics
from utils.languages import get_translation_for_key_localized as trl, get_language
from utils.logging_util import log_into_logs
from utils.per_user_settings import get_per_user_setting
from utils.tips import append_tip_to_message
from utils.tzutil import get_server_midnight_time


class ChatStreakStorage:
    """Chat Streaks Storage.
    Every member has 24 hours before their streak gets reset.
    If their streak day changes to the next day without expiring, they get congratulated.
    """

    def __init__(self) -> None:
        async def init_async():

            db = await get_conn()
            await db.execute(
                'CREATE TABLE IF NOT EXISTS chat_streaks (guild_id INTEGER, member_id INTEGER, last_message DATETIME, start_time DATETIME)')
            await db.execute(
                'CREATE UNIQUE INDEX IF NOT EXISTS chat_streaks_index ON chat_streaks (guild_id, member_id)')

            cur = await db.execute("SELECT * FROM chat_streaks WHERE typeof(last_message) != 'text' OR typeof(start_time) != 'text'")
            invalid_rows = await cur.fetchall()
            for row in invalid_rows:
                await db.execute("DELETE FROM chat_streaks WHERE guild_id = ? AND member_id = ?", (row[0], row[1]))

            await db.commit()
            await db.close()

        asyncio.get_event_loop().run_until_complete(init_async())

    async def set_streak(self, guild_id: int, member_id: int) -> tuple[str, int, int]:
        """Set streak

        Args:
            guild_id (int): Guild ID
            member_id (int): Member ID

        Returns:
            str: The state of the streak
        """

        db = await get_conn()

        # Check and start if not existant
        cur = await db.execute(
            'SELECT * FROM chat_streaks WHERE guild_id = ? AND member_id = ?', (guild_id, member_id))
        if await cur.fetchone() is None:
            start_time = get_server_midnight_time(guild_id)
            await db.execute('INSERT INTO chat_streaks (guild_id, member_id, last_message, start_time) VALUES (?, ?, ?, ?)',
                        (guild_id, member_id, start_time, start_time))
            await db.commit()
            await db.close()
            return "started", 0, 0

        cur = await db.execute('SELECT last_message, start_time FROM chat_streaks WHERE guild_id = ? AND member_id = ?',
                    (guild_id, member_id))
        result = await cur.fetchone()
        last_message = datetime.datetime.fromisoformat(result[0])
        start_time = datetime.datetime.fromisoformat(result[1])

        # Check for streak expiry
        if get_server_midnight_time(guild_id) - last_message > datetime.timedelta(days=1, hours=1):
            streak = max((last_message - start_time).days, 0)
            await db.execute(
                'UPDATE chat_streaks SET last_message = ?, start_time = ? WHERE guild_id = ? AND member_id = ?',
                (get_server_midnight_time(guild_id), get_server_midnight_time(guild_id), guild_id, member_id))
            await db.commit()
            await db.close()
            return "expired", streak, 0

        before_update = (last_message - start_time).days
        cur.execute('UPDATE chat_streaks SET last_message = ? WHERE guild_id = ? AND member_id = ?',
                    (get_server_midnight_time(guild_id), guild_id, member_id))
        after_update = (get_server_midnight_time(guild_id) - start_time).days

        cur.close()
        db.commit()

        if before_update != after_update:
            return "updated", before_update, after_update

        return "stayed", after_update, 0

    async def reset_streak(self, guild_id: int, member_id: int) -> None:
        """Reset streak

        Args:
            guild_id (int): Guild ID
            member_id (int): Member ID
        """

        db = await get_conn()
        cur = await db.execute(
            'SELECT * FROM chat_streaks WHERE guild_id = ? AND member_id = ?', (guild_id, member_id))
        if not await cur.fetchone():
            start_time = get_server_midnight_time(guild_id)
            await db.execute('INSERT INTO chat_streaks (guild_id, member_id, last_message, start_time) VALUES (?, ?, ?, ?)',
                        (guild_id, member_id, start_time, start_time))
            await db.commit()
            await db.close()
            return

        await db.execute('UPDATE chat_streaks SET last_message = ?, start_time = ? WHERE guild_id = ? AND member_id = ?',
                    (get_server_midnight_time(guild_id), get_server_midnight_time(guild_id), guild_id, member_id))
        await db.commit()
        await db.close()


class ChatStreaks(discord.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        super().__init__()
        self.bot = bot
        self.streak_storage = ChatStreakStorage()

    @discord.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        (state, old_streak, new_streak) = await self.streak_storage.set_streak(
            message.guild.id, message.author.id)

        if state == "expired":
            if old_streak == 0:
                return
            if get_per_user_setting(message.author.id, 'chat_streaks_alerts', 'on') == 'off':
                return
            msg = await message.reply(
                await trl(message.author.id, message.guild.id, "chat_streaks_expired").format(streak=old_streak))
            await msg.delete(delay=3)

        if state == "updated":
            if get_per_user_setting(message.author.id, 'chat_streaks_alerts', 'on') != 'on':
                return  # Only trigger if the user has the setting on
            msg = await message.reply(
                await trl(message.author.id, message.guild.id, "chat_streaks_updated").format(streak=new_streak))
            await msg.delete(delay=3)

    streaks_subcommand = discord.SlashCommandGroup(
        name='streaks', description='Manage the chat streaks')

    @streaks_subcommand.command(name="reset", description="Reset streak for a specific user")
    @commands_ext.guild_only()
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @discord.option(name='user', description='The user to reset the streak for', type=discord.Member)
    @analytics("streaks reset")
    async def reset_streak_command(self, ctx: discord.ApplicationContext, user: discord.Member):
        # Reset streak
        await self.streak_storage.reset_streak(ctx.guild.id, user.id)

        # Create a embed for logs
        logging_embed = discord.Embed(title=await trl(ctx.user.id, ctx.guild.id, "chat_streaks_reset_log_title"))
        logging_embed.add_field(name=await trl(ctx.user.id, ctx.guild.id, "chat_streaks_reset_log_admin"),
                                value=f'{ctx.user.mention}')
        logging_embed.add_field(name=await trl(ctx.user.id, ctx.guild.id, "logging_user"),
                                value=f'{user.mention}')

        # Send to log
        await log_into_logs(ctx.guild, logging_embed)

        # Respond
        await ctx.respond(await trl(ctx.user.id, ctx.guild.id, "chat_streaks_reset_success", append_tip=True).format(user=user.mention),
                          ephemeral=True)

    @streaks_subcommand.command(name="streak", description="Get someone's streak, to get yours, /streak.")
    @commands_ext.guild_only()
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @discord.option(name='user', description='The user to get the streak for', type=discord.Member)
    @analytics("streaks streak")
    async def get_user_streak(self, ctx: discord.ApplicationContext, user: discord.Member):
        (_, streak, _) = await self.streak_storage.set_streak(ctx.guild.id, user.id)
        await ctx.respond(
            await trl(ctx.user.id, ctx.guild.id, "chat_streaks_streak_admin", append_tip=True).format(user=user.mention, streak=str(streak)),
            ephemeral=True)

    @discord.slash_command(name='streak', description='Get your current streak')
    @analytics("streak")
    async def get_streak_command(self, ctx: discord.ApplicationContext):
        (_, streak, _) = self.streak_storage.set_streak(ctx.guild.id, ctx.user.id)
        await ctx.respond(await trl(ctx.user.id, ctx.guild.id, "chat_streaks_streak", append_tip=True).format(streak=streak), ephemeral=True)

    # Leaderboard

    @streaks_subcommand.command(name="leaderboard", description="Get the chat streak leaderboard")
    @commands_ext.guild_only()
    @analytics("streaks leaderboard")
    async def streaks_lb(self, ctx: discord.ApplicationContext):
        db = await get_conn()
        cur = await db.execute(
            'SELECT member_id, MAX(julianday(last_message) - julianday(start_time)) '
            'FROM chat_streaks '
            'WHERE guild_id = ? '
            'GROUP BY member_id '
            'ORDER BY MAX(julianday(last_message) - julianday(start_time)) DESC LIMIT 10',
            (ctx.guild.id,))
        rows = await cur.fetchall()
        await db.close()

        message = await trl(ctx.user.id, ctx.guild.id, "chat_streak_leaderboard_title")

        for i, row in enumerate(rows):
            member = ctx.guild.get_member(row[0])
            if member is None:
                continue

            days = int(row[1])

            message += await trl(ctx.user.id, ctx.guild.id, "chat_streak_leaderboard_line").format(position=i + 1,
                                                                                             user=member.mention,
                                                                                             days=str(days))

        if get_per_user_setting(ctx.user.id, 'tips_enabled', 'true') == 'true':
            language = get_language(ctx.guild.id, ctx.user.id)
            message = append_tip_to_message(ctx.guild.id, ctx.user.id, message, language)
        await ctx.respond(message, ephemeral=True)
