import datetime

import discord
from discord.ext import commands as commands_ext

from database import conn as db
from utils.analytics import analytics
from utils.blocked import is_blocked
from utils.settings import get_setting, set_setting
from utils.logging import log_into_logs
from utils.chat_streak_util import get_time_at_midnight


class ChatStreakStorage:
    """Chat Streaks Storage.
    Every member has 24 hours before their streak gets reset.
    If their streak day changes to the next day without expiring, they get congratulated.
    """

    def __init__(self) -> None:
        cur = db.cursor()
        cur.execute(
            'CREATE TABLE IF NOT EXISTS chat_streaks (guild_id INTEGER, member_id INTEGER, last_message DATETIME, start_time DATETIME)')
        cur.execute(
            'CREATE UNIQUE INDEX IF NOT EXISTS chat_streaks_index ON chat_streaks (guild_id, member_id)')

        cur.execute("SELECT * FROM chat_streaks WHERE typeof(last_message) != 'text' OR typeof(start_time) != 'text'")
        invalid_rows = cur.fetchall()
        for row in invalid_rows:
            cur.execute("DELETE FROM chat_streaks WHERE guild_id = ? AND member_id = ?", (row[0], row[1]))

        cur.close()
        db.commit()

    def set_streak(self, guild_id: int, member_id: int) -> tuple[str, int, int]:
        """Set streak

        Args:
            guild_id (int): Guild ID
            member_id (int): Member ID

        Returns:
            str: The state of the streak
        """

        cur = db.cursor()

        # Check and start if not existant
        cur.execute(
            'SELECT * FROM chat_streaks WHERE guild_id = ? AND member_id = ?', (guild_id, member_id))
        if cur.fetchone() is None:
            start_time = get_time_at_midnight()
            cur.execute('INSERT INTO chat_streaks (guild_id, member_id, last_message, start_time) VALUES (?, ?, ?, ?)',
                        (guild_id, member_id, start_time, start_time))
            cur.close()
            db.commit()
            return "started", 0, 0

        cur.execute('SELECT last_message, start_time FROM chat_streaks WHERE guild_id = ? AND member_id = ?',
                    (guild_id, member_id))
        result = cur.fetchone()
        last_message = datetime.datetime.fromisoformat(result[0])
        start_time = datetime.datetime.fromisoformat(result[1])

        # Check for streak expiry
        if get_time_at_midnight() - last_message > datetime.timedelta(days=1, hours=1):
            streak = max((last_message - start_time).days, 0)
            cur.execute(
                'UPDATE chat_streaks SET last_message = ?, start_time = ? WHERE guild_id = ? AND member_id = ?',
                (get_time_at_midnight(), get_time_at_midnight(), guild_id, member_id))
            cur.close()
            db.commit()
            return "expired", streak, 0

        before_update = (last_message - start_time).days
        cur.execute('UPDATE chat_streaks SET last_message = ? WHERE guild_id = ? AND member_id = ?',
                    (get_time_at_midnight(), guild_id, member_id))
        after_update = (get_time_at_midnight() - start_time).days

        cur.close()
        db.commit()

        if before_update != after_update:
            return "updated", before_update, after_update

        return "stayed", after_update, 0

    def reset_streak(self, guild_id: int, member_id: int) -> None:
        """Reset streak

        Args:
            guild_id (int): Guild ID
            member_id (int): Member ID
        """

        cur = db.cursor()
        cur.execute(
            'SELECT * FROM chat_streaks WHERE guild_id = ? AND member_id = ?', (guild_id, member_id))
        if not cur.fetchone():
            start_time = get_time_at_midnight()
            cur.execute('INSERT INTO chat_streaks (guild_id, member_id, last_message, start_time) VALUES (?, ?, ?, ?)',
                        (guild_id, member_id, start_time, start_time))
            cur.close()
            db.commit()
            return

        cur.execute('UPDATE chat_streaks SET last_message = ?, start_time = ? WHERE guild_id = ? AND member_id = ?',
                    (get_time_at_midnight(), get_time_at_midnight(), guild_id, member_id))
        cur.close()
        db.commit()


class ChatStreaks(discord.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        super().__init__()
        self.bot = bot
        self.streak_storage = ChatStreakStorage()

    @discord.Cog.listener()
    @is_blocked()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        (state, old_streak, new_streak) = self.streak_storage.set_streak(
            message.guild.id, message.author.id)

        if get_setting(message.guild.id, 'chat_streak_alerts', 'true') == 'true':
            if state == "expired":
                if old_streak == 0:
                    return
                msg = await message.channel.send(f'Your streak of {old_streak:d} days has expired :<')
                await msg.delete(delay=5)

            if state == "updated":
                msg = await message.channel.send(f'{new_streak:d} days of consecutive  messages! Keep it up :3')
                await msg.delete(delay=5)

    streaks_subcommand = discord.SlashCommandGroup(
        name='streaks', description='Manage the chat streaks')

    @streaks_subcommand.command(name="alerts", description="Show/hide the chat streak alerts")
    @commands_ext.guild_only()
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @is_blocked()
    @analytics("streaks alerts")
    async def toggle_alerts(self, ctx: discord.ApplicationContext, value: bool):
        # Get old value
        old_value = get_setting(ctx.guild.id, "chat_streak_alerts", str(value)) == "True"

        # Determine if the value has changed and update accordingly
        if old_value != value:
            logging_embed = discord.Embed(title="Chat Streaks alerts changed")
            logging_embed.add_field(name="User", value=f"{ctx.user.mention}")
            logging_embed.add_field(name="Value", value=f'{"Yes" if old_value else "No"} -> {"Yes" if value else "No"}')

        # Save settings value
        set_setting(ctx.guild.id, 'chat_streak_alerts', str(value))

        # Respond
        await ctx.respond(
            'Succcessfully turned on chat streak alerts' if value else 'Successfully turned off chat streak alerts',
            ephemeral=True)

    @streaks_subcommand.command(name="list", description="List the chat streak options.")
    @commands_ext.guild_only()
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @is_blocked()
    @analytics("streaks list")
    async def list_settings(self, ctx: discord.ApplicationContext):
        alerts = get_setting(ctx.guild.id, 'chat_streak_alerts', 'true')

        embed = discord.Embed(title='Chat Streak settings',
                              color=discord.Color.blurple())
        embed.add_field(name='Chat Streak Alerts', value=alerts)

        await ctx.respond(embed=embed, ephemeral=True)

    @streaks_subcommand.command(name="reset", description="Reset streak for a specific user")
    @commands_ext.guild_only()
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @discord.option(name='user', description='The user to reset the streak for', type=discord.Member)
    @is_blocked()
    @analytics("streaks reset")
    async def reset_streak_command(self, ctx: discord.ApplicationContext, user: discord.Member):
        # Reset streak
        self.streak_storage.reset_streak(ctx.guild.id, user.id)

        # Create a embed for logs
        logging_embed = discord.Embed(title="Chat Streak reset")
        logging_embed.add_field(name="Admin", value=f'{ctx.user.mention}')
        logging_embed.add_field(name="Target", value=f'{user.mention}')

        # Send to log
        await log_into_logs(ctx.guild, logging_embed)

        # Respond
        await ctx.respond(f'Successfully reset the streak for {user.mention}.', ephemeral=True)

    @streaks_subcommand.command(name="streak", description="Get someone's streak, to get yours, /streak.")
    @commands_ext.guild_only()
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @discord.option(name='user', description='The user to get the streak for', type=discord.Member)
    @is_blocked()
    @analytics("streaks streak")
    async def get_user_streak(self, ctx: discord.ApplicationContext, user: discord.Member):
        (_, streak, _) = self.streak_storage.set_streak(ctx.guild.id, user.id)
        await ctx.respond(f'{user.mention}\'s current streak is {streak} days.', ephemeral=True)

    @discord.slash_command(name='streak', description='Get your current streak')
    @is_blocked()
    @analytics("streak")
    async def get_streak_command(self, ctx: discord.ApplicationContext):
        (_, streak, _) = self.streak_storage.set_streak(ctx.guild.id, ctx.user.id)
        await ctx.respond(f'Your current streak is {streak} days.', ephemeral=True)

    # Leaderboard

    @streaks_subcommand.command(name="leaderboard", description="Get the chat streak leaderboard")
    @commands_ext.guild_only()
    @is_blocked()
    @analytics("streaks leaderboard")
    async def streaks_lb(self, ctx: discord.ApplicationContext):
        cur = db.cursor()
        cur.execute(
            'SELECT member_id, MAX(julianday(last_message) - julianday(start_time)) FROM chat_streaks WHERE guild_id = ? GROUP BY member_id ORDER BY MAX(julianday(last_message) - julianday(start_time)) DESC LIMIT 10',
            (ctx.guild.id,))
        rows = cur.fetchall()
        cur.close()

        message = "# Chat Streak Leaderboard\n\n"

        for i, row in enumerate(rows):
            member = ctx.guild.get_member(row[0])
            if member is None:
                continue
            message += f"{i + 1}. {member.mention} - {row[1]:.0f} days\n"

        await ctx.respond(message, ephemeral=True)
