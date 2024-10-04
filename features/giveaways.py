import datetime
import random

import discord
from bson import ObjectId
from discord.ext import commands as commands_ext
from discord.ext import tasks

from database import client
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

        res = client['Giveaways'].insert_one(
            {'ChannelID': ctx.channel.id, 'MessageID': msg1.id, 'Item': item, 'EndDate': end_date.isoformat(),
             'Winners': winners})

        # Send success message
        await ctx.respond(
            trl(ctx.user.id, ctx.guild.id, "giveaways_new_success", append_tip=True).format(id=str(res.inserted_id)),
            ephemeral=True)

    @giveaways_group.command(name="end", description="End a giveaway IRREVERSIBLY")
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.bot_has_guild_permissions(add_reactions=True, read_message_history=True, send_messages=True)
    @commands_ext.guild_only()
    @discord.option("giveaway_id", "The ID of the giveaway to end. Given when creating a giveaway.")
    @analytics("giveaway end")
    async def giveaway_end(self, ctx: discord.ApplicationContext, giveaway_id: str):
        if not ObjectId.is_valid(giveaway_id):
            await ctx.respond(trl(ctx.user.id, ctx.guild.id, "giveaways_error_not_found"), ephemeral=True)
            return

        res = client['Giveaways'].count_documents({'_id': ObjectId(giveaway_id)})
        if res == 0:
            await ctx.respond(trl(ctx.user.id, ctx.guild.id, "giveaways_error_not_found"), ephemeral=True)
            return

        await self.process_send_giveaway(giveaway_id)

        await ctx.respond(trl(ctx.user.id, ctx.guild.id, "giveaways_giveaway_end_success", append_tip=True),
                          ephemeral=True)

    @giveaways_group.command(name='list', description='List all giveaways')
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @analytics("giveaway list")
    async def giveaway_list(self, ctx: discord.ApplicationContext):
        res = client['Giveaways'].find({}).to_list()

        message = trl(ctx.user.id, ctx.guild.id, "giveaways_list_title")

        for i in res:
            id = str(i['_id'])
            item = i['Item']
            winners = i['Winners']
            time_remaining = datetime.datetime.fromisoformat(i['EndDate']) - get_now_for_server(ctx.guild.id)
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

        client['Giveaways'].update_one({'MessageID': reaction.message.id}, {'$push': {'Participants': user.id}})


    @discord.Cog.listener()
    async def on_reaction_remove(self, reaction: discord.Reaction, user: discord.User):
        if user.bot:
            return

        client['Giveaways'].update_one({'MessageID': reaction.message.id}, {'$pull': {'Participants': user.id}})

    async def process_send_giveaway(self, giveaway_id: str):
        res = client['Giveaways'].find_one({'_id': ObjectId(giveaway_id)})
        if not res:
            return

        # Fetch the channel and message
        chan = await self.bot.fetch_channel(res['ChannelID'])
        msg = await chan.fetch_message(res['MessageID'])

        users = res['Participants']

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

        client['Giveaways'].delete_one({'_id': ObjectId(giveaway_id)})

    @tasks.loop(minutes=1)
    async def giveaway_mng(self):
        res = client['Giveaways'].find({}).to_list()
        for i in res:
            channel_id = i['ChannelID']
            channel = await self.bot.fetch_channel(channel_id)

            time = datetime.datetime.now(datetime.UTC)
            if channel is not None:
                time = get_now_for_server(channel.guild.id)
            # Check if the giveaway ended
            end_date = datetime.datetime.fromisoformat(i['EndTime'])
            if time > end_date:
                await self.process_send_giveaway(str(i['_id']))
