import datetime
import random

import discord
from discord.ext import commands as commands_ext
from database import conn
from utils.analytics import analytics
from utils.blocked import is_blocked
from discord.ext import tasks


class Giveaways(discord.Cog):
    giveaways_group = discord.SlashCommandGroup(name="giveaways")

    def __init__(self, bot: discord.Bot):
        self.bot = bot
        cur = conn.cursor()
        cur.execute(
            "create table if not exists giveaways(id integer primary key, channel_id int, message_id int, item text, end_date text, winner_count int)"
        )
        cur.execute(
            "create table if not exists giveaway_participants(id integer primary key, giveaway_id integer, user_id text)"
        )

        # Add winner_count column if it doesn't exist
        cur.execute(
            "PRAGMA table_info(giveaways)"
        )
        columns = cur.fetchall()
        column_names = [column[1] for column in columns]
        if "winner_count" not in column_names:
            cur.execute(
                "ALTER TABLE giveaways ADD COLUMN winner_count int"
            )

        # Update giveaway_participants table to have user_id as text
        cur.execute(
            "PRAGMA table_info(giveaway_participants)"
        )
        columns = cur.fetchall()
        column_names = [column[1] for column in columns]
        if "user_id" in column_names:
            cur.execute(
                "ALTER TABLE giveaway_participants RENAME TO giveaway_participants_old"
            )
            cur.execute(
                "create table giveaway_participants(id integer primary key, giveaway_id integer, user_id text)"
            )
            cur.execute(
                "insert into giveaway_participants(giveaway_id, user_id) select giveaway_id, cast(user_id as text) from giveaway_participants_old"
            )
            cur.execute(
                "drop table giveaway_participants_old"
            )

        conn.commit()

        self.giveaway_mng.start()

    @giveaways_group.command(name="new", description="Create a new giveaway")
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.bot_has_guild_permissions(add_reactions=True, read_message_history=True, send_messages=True)
    @commands_ext.guild_only()
    @is_blocked()
    @analytics("giveaway new")
    async def giveaway_new(self, ctx: discord.ApplicationContext, item: str, days: int, hours: int, minutes: int, winners: int):
        # Check if the parameters are correct
        if days + hours < 0 or days < 0 or hours < 0 or minutes < 0 or winners < 0:
            await ctx.respond("Parameters must be positive", ephemeral=True)
            return

        # Determine ending date
        end_date = datetime.datetime.now(datetime.UTC)
        end_date = end_date + datetime.timedelta(days=days, hours=hours, minutes=minutes)

        # Send message
        msg1 = await ctx.channel.send(f"GIVEAWAY! {item}")
        await msg1.add_reaction("🎉")

        # Register giveaway
        cur = conn.cursor()
        cur.execute("insert into giveaways(channel_id, message_id, item, end_date, winner_count) values(?, ?, ?, ?, ?)",
                    (ctx.channel.id, msg1.id, item, end_date.isoformat(), winners))

        conn.commit()

        # Send success message
        await ctx.respond(f"Created giveaway successfully! Giveaway ID is {str(cur.lastrowid)}", ephemeral=True)

    @giveaways_group.command(name="end", description="End a giveaway IRREVERSIBLY")
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.bot_has_guild_permissions(add_reactions=True, read_message_history=True, send_messages=True)
    @commands_ext.guild_only()
    @is_blocked()
    @analytics("giveaway end")
    async def giveaway_end(self, ctx: discord.ApplicationContext, giveaway_id: int):
        cur = conn.cursor()

        # Verify if the giveaway exists
        cur.execute("select * from giveaways where id=?", (giveaway_id,))
        res = cur.fetchone()
        if res is None:
            await ctx.respond("Giveaway not found", ephemeral=True)
            return
        
        await self.process_send_giveaway(giveaway_id)

        await ctx.respond("Ended giveaway successfully!", ephemeral=True)

    @discord.Cog.listener()
    @is_blocked()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        if user.bot:
            return

        cur = conn.cursor()

        # Verify if it's a valid message
        cur.execute("select * from giveaways where message_id=?", (reaction.message.id,))
        res = cur.fetchone()
        if res is None:
            return

        # Add user to participants of giveaway
        cur.execute("insert into giveaway_participants(giveaway_id, user_id) values(?, ?)", (res[0], str(user.id)))

        conn.commit()

    @discord.Cog.listener()
    @is_blocked()
    async def on_reaction_remove(self, reaction: discord.Reaction, user: discord.User):
        if user.bot:
            return

        cur = conn.cursor()

        # Verify if it's a valid message
        cur.execute("select * from giveaways where message_id=?", (reaction.message.id,))
        res = cur.fetchone()
        if res is None:
            return

        # Remove user from participants of giveaway
        cur.execute("delete from giveaway_participants where giveaway_id=? and user_id=?", (res[0], str(user.id)))

        conn.commit()

    async def process_send_giveaway(self, giveaway_id: int):
        cur = conn.cursor()

        cur.execute("select * from giveaways where id=?", (giveaway_id,))
        res = cur.fetchone()
        if res is None:
            return
        
        # Delete giveaway from database
        cur.execute("delete from giveaways where id=?", (giveaway_id,))
        
        # Fetch the channel and message
        chan = await self.bot.fetch_channel(res[1])
        msg = await chan.fetch_message(res[2])

        # List people that joined the giveaway
        cur.execute("select * from giveaway_participants where giveaway_id=?", (giveaway_id,))
        users = [j[2] for j in cur.fetchall()]

        # Check if there are enough members to select winners
        if len(users) < res[5]:
            await chan.send("Not enough participants to select winners. Selecting all participants as winners.")
            winners = users
        else:
            # Determine winners
            winners = random.sample(users, res[5])

        # Get channel and send message
        await chan.send(content=f"The winner{'' if len(winners) == 1 else 's'} of {res[3]} is {', '.join([f'<@{j}>' for j in winners])}")

        # Remove all giveaway participants from the database
        cur.execute("delete from giveaway_participants where giveaway_id=?", (giveaway_id,))

    @tasks.loop(minutes=1)
    async def giveaway_mng(self):
        cur = conn.cursor()

        cur.execute("select * from giveaways")
        for i in cur.fetchall():
            # Check if the giveaway ended
            end_date = datetime.datetime.fromisoformat(i[4])
            if datetime.datetime.now(datetime.UTC) > end_date:
                await self.process_send_giveaway(i[0])
