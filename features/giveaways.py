import datetime
import random

import discord
from discord.ext import commands as commands_ext
from discord.ext import tasks

from database import conn
from utils.analytics import analytics
from utils.generic import pretty_time_delta
from utils.languages import get_translation_for_key_localized as trl, get_language
from utils.per_user_settings import get_per_user_setting
from utils.tips import append_tip_to_message
from utils.tzutil import get_now_for_server


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

        self.giveaway_mng.start()

    @giveaways_group.command(name="new", description="Create a new giveaway")
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.bot_has_guild_permissions(add_reactions=True, read_message_history=True, send_messages=True)
    @commands_ext.guild_only()
    @discord.option(name='item', description='The item to give away, PUBLICLY VISIBLE!')
    @discord.option(name='days',
                    description='Number of days until the giveaway ends. Adds up with other time parameters')
    @discord.option(name='hours',
                    description='Number of hours until the giveaway ends. Adds up with other time parameters')
    @discord.option(name='minutes',
                    description='Number of minutes until the giveaway ends. Adds up with other time parameters')
    @discord.option(name='winners', description='Number of winners')
    @analytics("giveaway new")
    async def giveaway_new(self, ctx: discord.ApplicationContext, item: str, days: int, hours: int, minutes: int,
                           winners: int):
        # Check if the parameters are correct
        if days + hours < 0 or days < 0 or hours < 0 or minutes < 0 or winners < 0:
            await ctx.respond(trl(ctx.user.id, ctx.guild.id, "giveaways_error_negative_parameters"), ephemeral=True)
            return

        # Determine ending date
        end_date = get_now_for_server(ctx.guild.id)
        end_date = end_date + datetime.timedelta(days=days, hours=hours, minutes=minutes)

        # Send message
        msg1 = await ctx.channel.send(trl(0, ctx.guild.id, "giveaways_giveaway_text").format(item=item))
        await msg1.add_reaction("🎉")

        # Register giveaway
        cur = conn.cursor()
        cur.execute("insert into giveaways(channel_id, message_id, item, end_date, winner_count) values(?, ?, ?, ?, ?)",
                    (ctx.channel.id, msg1.id, item, end_date.isoformat(), winners))

        conn.commit()

        # Send success message
        await ctx.respond(trl(ctx.user.id, ctx.guild.id, "giveaways_new_success", append_tip=True).format(id=cur.lastrowid),
                          ephemeral=True)

    @giveaways_group.command(name="end", description="End a giveaway IRREVERSIBLY")
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.bot_has_guild_permissions(add_reactions=True, read_message_history=True, send_messages=True)
    @commands_ext.guild_only()
    @discord.option("giveaway_id", "The ID of the giveaway to end. Given when creating a giveaway.")
    @analytics("giveaway end")
    async def giveaway_end(self, ctx: discord.ApplicationContext, giveaway_id: int):
        cur = conn.cursor()

        # Verify if the giveaway exists
        cur.execute("select * from giveaways where id=?", (giveaway_id,))
        res = cur.fetchone()
        if res is None:
            await ctx.respond(trl(ctx.user.id, ctx.guild.id, "giveaways_error_not_found"), ephemeral=True)
            return

        await self.process_send_giveaway(giveaway_id)

        await ctx.respond(trl(ctx.user.id, ctx.guild.id, "giveaways_giveaway_end_success", append_tip=True), ephemeral=True)

    @giveaways_group.command(name='list', description='List all giveaways')
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @analytics("giveaway list")
    async def giveaway_list(self, ctx: discord.ApplicationContext):
        cur = conn.cursor()

        # Get all giveaways
        cur.execute("select * from giveaways")
        res = cur.fetchall()

        message = trl(ctx.user.id, ctx.guild.id, "giveaways_list_title")

        for i in res:
            id = i[0]
            item = i[3]
            winners = i[5]
            time_remaining = datetime.datetime.fromisoformat(i[4]) - get_now_for_server(ctx.guild.id)
            time_remaining = time_remaining.total_seconds()
            time_remaining = pretty_time_delta(time_remaining, user_id=ctx.user.id, server_id=ctx.guild.id)

            message += trl(ctx.user.id, ctx.guild.id, "giveaways_list_line").format(id=id, item=item,
                                                                                    winners=winners,
                                                                                    time=time_remaining)

        if len(res) == 0:
            message += trl(ctx.user.id, ctx.guild.id, "giveaways_list_empty")

        if get_per_user_setting(ctx.user.id, 'tips_enabled', 'true') == 'true':
            language = get_language(ctx.guild.id, ctx.user.id)
            message = append_tip_to_message(ctx.guild.id, ctx.user.id, message, language)
        await ctx.respond(message, ephemeral=True)

    @discord.Cog.listener()
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

        # Fetch the channel and message
        chan = await self.bot.fetch_channel(res[1])
        msg = await chan.fetch_message(res[2])

        # List people that joined the giveaway
        cur.execute("select * from giveaway_participants where giveaway_id=?", (giveaway_id,))
        users = [j[2] for j in cur.fetchall()]

        # Check if there are enough members to select winners
        if len(users) < res[5]:
            await chan.send(trl(0, chan.guild.id, "giveaways_warning_not_enough_participants"))
            winners = users
        else:
            # Determine winners
            winners = random.sample(users, res[5])

        # Get channel and send message
        if len(winners) == 1:
            msg2 = trl(0, chan.guild.id, "giveaways_winner").format(item=res[3], mention=f"<@{winners[0]}>")
            await chan.send(msg2)
        else:
            mentions = ", ".join([f"<@{j}>" for j in winners])
            last_mention = mentions.rfind(", ")
            last_mention = mentions[last_mention + 2:]
            mentions = mentions[:last_mention]
            msg2 = trl(0, chan.guild.id, "giveaways_winners").format(item=res[3],
                                                                     mentions=mentions,
                                                                     last_mention=last_mention)
            await chan.send(msg2)

        # Delete giveaway from database
        cur.execute("delete from giveaways where id=?", (giveaway_id,))
        # Remove all giveaway participants from the database
        cur.execute("delete from giveaway_participants where giveaway_id=?", (giveaway_id,))

    @tasks.loop(minutes=1)
    async def giveaway_mng(self):
        cur = conn.cursor()

        cur.execute("select * from giveaways")
        for i in cur.fetchall():
            channel_id = i[1]
            channel = await self.bot.fetch_channel(channel_id)

            time = datetime.datetime.now(datetime.UTC)
            if channel is not None:
                time = get_now_for_server(channel.guild.id)
            # Check if the giveaway ended
            end_date = datetime.datetime.fromisoformat(i[4])
            if time > end_date:
                await self.process_send_giveaway(i[0])
