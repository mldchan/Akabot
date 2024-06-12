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
            "create table if not exists giveaways(id integer primary key, channel_id int, message_id int, item text, end_date text)")
        cur.execute(
            "create table if not exists giveaway_participants(id integer primary key, giveaway_id integer, user_id integer)")

        conn.commit()

        self.giveaway_mng.start()

    @giveaways_group.command(name="new", description="Create a new giveaway")
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.bot_has_guild_permissions(add_reactions=True, read_message_history=True, send_messages=True)
    @commands_ext.guild_only()
    @is_blocked()
    @analytics("giveaway new")
    async def giveaway_new(self, ctx: discord.ApplicationContext, item: str, days: int, hours: int):
        # Check if the parameters are correct
        if days + hours < 0 or days < 0 or hours < 0:
            await ctx.respond("Parameters must be positive", ephemeral=True)
            return

        # Determine ending date
        end_date = datetime.datetime.now(datetime.UTC)
        end_date = end_date + datetime.timedelta(days=days, hours=hours)

        # Send message
        msg1 = await ctx.channel.send(f"GIVEAWAY! {item}")
        await msg1.add_reaction("🎉")

        # Register giveaway
        cur = conn.cursor()
        cur.execute("insert into giveaways(channel_id, message_id, item, end_date) values(?, ?, ?, ?)",
                    (ctx.channel.id, msg1.id, item, end_date.isoformat()))

        conn.commit()

        # Send success message
        await ctx.respond("Created giveaway successfully!", ephemeral=True)

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
        cur.execute("insert into giveaway_participants(giveaway_id, user_id) values(?, ?)", (res[0], user.id))

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
        cur.execute("delete from giveaway_participants where giveaway_id=? and user_id=?", (res[0], user.id))

        conn.commit()

    @tasks.loop(minutes=1)
    async def giveaway_mng(self):
        cur = conn.cursor()

        cur.execute("select * from giveaways")
        for i in cur.fetchall():
            # Check if the giveaway ended
            end_date = datetime.datetime.fromisoformat(i[4])
            if datetime.datetime.now(datetime.UTC) > end_date:
                cur.execute("delete from giveaways where id=?", (i[0],))

                # List people that joined the giveaway
                cur.execute("select * from giveaway_participants where giveaway_id=?", (i[0],))
                users = [j[2] for j in cur.fetchall()]

                # Determine winner
                winner = random.choice(users)

                # Get channel and send message
                chan = await self.bot.fetch_channel(i[1])
                await chan.send(content=f"The winner of {i[3]} is <@{winner}>!")

                # Remove all giveaway participants from the database
                cur.execute("delete from giveaway_participants where giveaway_id=?", (i[0],))
