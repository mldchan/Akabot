import time

import discord
from discord.ext import commands as commands_ext
from discord.ext import tasks

from database import client
from utils.analytics import analytics
from utils.languages import get_translation_for_key_localized as trl
from utils.logging_util import log_into_logs


class ChatRevive(discord.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @discord.Cog.listener()
    async def on_ready(self):
        self.revive_channels.start()

    @discord.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        client['ChatRevive'].update_one({'GuildID': str(message.guild.id), 'ChannelID': str(message.channel.id)},
                                        {'$set': {'LastMessage': time.time(), 'Revived': False}})

    @tasks.loop(minutes=1)
    async def revive_channels(self):
        for guild in self.bot.guilds:
            data = client['ChatRevive'].find({'GuildID': str(guild.id)}).to_list()
            for revive_channel in data:
                if revive_channel['Revived']:
                    continue

                if time.time() - revive_channel['LastMessage'] > revive_channel['RevivalTime']:
                    role = guild.get_role(int(revive_channel['RoleID']))
                    if role is None:
                        continue

                    channel = guild.get_channel(int(revive_channel['ChannelID']))
                    if channel is None:
                        continue

                    if not channel.can_send():
                        continue

                    await channel.send(f'{role.mention}, this channel has been inactive for a while.')
                    client['ChatRevive'].update_one({'GuildID': str(guild.id), 'ChannelID': str(channel.id)},
                                                    {'$set': {'Revived': True}})

    chat_revive_subcommand = discord.SlashCommandGroup(name='chatrevive', description='Revive channels')

    @chat_revive_subcommand.command(name="set", description="Set revive settings for a channel")
    @commands_ext.guild_only()
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.bot_has_permissions(send_messages=True)
    @analytics("chatrevive set")
    async def set_revive_settings(self, ctx: discord.ApplicationContext, channel: discord.TextChannel,
                                  revival_minutes: int,
                                  revival_role: discord.Role):

        # Permission checks
        if not revival_role.mentionable and not ctx.guild.me.guild_permissions.manage_roles:
            await ctx.respond(trl(ctx.user.id, ctx.guild.id, "chat_revive_set_error_not_mentionable"),
                              ephemeral=True)
            return

        # Database access

        # Delete existing record
        client['ChatRevive'].delete_one({'GuildID': str(ctx.guild.id), 'ChannelID': str(channel.id)})

        # Set new one
        client['ChatRevive'].insert_one({'GuildID': str(ctx.guild.id), 'ChannelID': str(channel.id), 'RoleID': str(revival_role.id),
                                         'RevivalTime': revival_minutes * 60, 'LastMessage': time.time(),
                                         'Revived': False})

        # Embed for logs
        logging_embed = discord.Embed(title=trl(ctx.user.id, ctx.guild.id, "chat_revive_log_set_title"))
        logging_embed.add_field(name=trl(ctx.user.id, ctx.guild.id, "logging_channel"),
                                value=f"{ctx.channel.mention}", inline=True)
        logging_embed.add_field(name=trl(ctx.user.id, ctx.guild.id, "logging_user"),
                                value=f"{ctx.user.mention}", inline=True)
        logging_embed.add_field(name=trl(ctx.user.id, ctx.guild.id, "chat_revive_list_role"),
                                value=f"{revival_role.mention}", inline=False)
        logging_embed.add_field(name=trl(ctx.user.id, ctx.guild.id, "chat_revive_log_set_revival_time"),
                                value=trl(ctx.user.id, ctx.guild.id, "chat_revive_log_set_revival_time_value").format(
                                    time=str(revival_minutes)), inline=True)

        # Send to logs
        await log_into_logs(ctx.guild, logging_embed)

        # Send back response
        await ctx.respond(
            trl(ctx.user.id, ctx.guild.id, "chat_revive_set_response_success").format(channel=channel.mention),
            ephemeral=True)

    @chat_revive_subcommand.command(name="remove", description="List the revive settings")
    @commands_ext.guild_only()
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @analytics("chatrevive remove")
    async def remove_revive_settings(self, ctx: discord.ApplicationContext, channel: discord.TextChannel):
        client['ChatRevive'].delete_one({'GuildID': str(ctx.guild.id), 'ChannelID': str(channel.id)})

        # Create embed
        logging_embed = discord.Embed(title=trl(ctx.user.id, ctx.guild.id, "chat_revive_remove_log_title"))
        logging_embed.add_field(name=trl(ctx.user.id, ctx.guild.id, "logging_channel"),
                                value=f"{ctx.channel.mention}", inline=True)
        logging_embed.add_field(name=trl(ctx.user.id, ctx.guild.id, "logging_user"),
                                value=f"{ctx.user.mention}", inline=True)

        # Send to logs
        await log_into_logs(ctx.guild, logging_embed)

        # Respond
        await ctx.respond(trl(ctx.user.id, ctx.guild.id, "chat_revive_remove_success").format(channel=channel.mention),
                          ephemeral=True)

    @chat_revive_subcommand.command(name="list", description="List the revive settings")
    @commands_ext.guild_only()
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @analytics("chatrevive list")
    async def list_revive_settings(self, ctx: discord.ApplicationContext, channel: discord.TextChannel):
        result = client['ChatRevive'].find_one({'GuildID': str(ctx.guild.id), 'ChannelID': str(channel.id)})

        if not result:
            await ctx.respond(trl(ctx.user.id, ctx.guild.id, "chat_revive_list_empty").format(channel=channel.mention),
                              ephemeral=True)
            return

        role = ctx.guild.get_role(int(result['RoleID']))

        embed = discord.Embed(title=trl(ctx.user.id, ctx.guild.id, "chat_revive_list_title").format(name=channel.name),
                              color=discord.Color.blurple())
        embed.add_field(name=trl(ctx.user.id, ctx.guild.id, "chat_revive_list_role"), value=role.mention)
        embed.add_field(name=trl(ctx.user.id, ctx.guild.id, "chat_revive_list_time"), value=str(result['RevivalTime']))

        await ctx.respond(embed=embed, ephemeral=True)
