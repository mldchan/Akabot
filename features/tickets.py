import datetime

import discord
from discord.ext import commands, tasks

from database import client
from utils.settings import set_setting, get_setting
from utils.tzutil import get_now_for_server
from utils.logging_util import log_into_logs


def db_add_ticket_channel(guild_id: int, ticket_category: int, user_id: int):
    client['TicketChannels'].insert_one({'GuildID': str(guild_id), 'TicketChannelID': str(ticket_category), 'UserID': str(user_id), 'MTime': get_now_for_server(guild_id), 'ATime': 'None'})


def db_is_ticket_channel(guild_id: int, ticket_channel_id: int):
    count = client['TicketChannels'].count_documents({'GuildID': str(guild_id), 'TicketChannelID': str(ticket_channel_id)})
    return count > 0


def db_get_ticket_creator(guild_id: int, ticket_channel_id: int) -> int:
    user_id = client['TicketChannels'].find_one({'GuildID': str(guild_id), 'TicketChannelID': str(ticket_channel_id)})['UserID']
    return int(user_id)


def db_remove_ticket_channel(guild_id: int, ticket_channel_id: int):
    client['TicketChannels'].delete_one({'GuildID': str(guild_id), 'TicketChannelID': str(ticket_channel_id)})


def db_update_mtime(guild_id: int, ticket_channel_id: int):
    client['TicketChannels'].update_one({'GuildID': str(guild_id), 'TicketChannelID': str(ticket_channel_id)}, {'$set': {'MTime': get_now_for_server(guild_id)}})


def check_ticket_archive_time(guild_id: int, ticket_channel_id: int) -> bool:
    archive_time = get_setting(guild_id, "ticket_archive_time", "0")  # hours
    if archive_time == "0":
        return False

    mtime = client['TicketChannels'].find_one({'GuildID': str(guild_id), 'TicketChannelID': str(ticket_channel_id)})['MTime']

    if mtime is None:
        return False

    if (get_now_for_server(guild_id) - mtime).total_seconds() / 3600 >= int(archive_time):
        return True

    return False


def db_is_archived(guild_id: int, ticket_channel_id: int) -> bool:
    atime = client['TicketChannels'].find_one({'GuildID': str(guild_id), 'TicketChannelID': str(ticket_channel_id)})['ATime']
    return atime != "None"


def check_ticket_hide_time(guild_id: int, ticket_channel_id: int) -> bool:
    if not db_is_archived(guild_id, ticket_channel_id):
        return False

    hide_time = get_setting(guild_id, "ticket_hide_time", "0")  # hours, hide time from archive
    if hide_time == "0":
        return False

    atime = client['TicketChannels'].find_one({'GuildID': str(guild_id), 'TicketChannelID': str(ticket_channel_id)})['ATime']

    if atime == 'None':
        return False

    if (get_now_for_server(guild_id) - atime).total_seconds() / 3600 >= int(hide_time):
        return True

    return False


def db_archive_ticket(guild_id: int, ticket_channel_id: int):
    client['TicketChannels'].update_one({'GuildID': str(guild_id), 'TicketChannelID': str(ticket_channel_id)}, {'$set': {'ATime': get_now_for_server(guild_id)}})


def db_list_archived_tickets():
    """
    Get all archived tickets.
    :return: List of tuples with guild_id and ticket_channel_id.
    """
    tickets = client['TicketChannels'].find({'ATime': {'$not': {'$eq': 'None'}}})
    return tickets


def db_list_not_archived_tickets():
    """
    Get all not archived tickets.
    :return: List of tuples with guild_id and ticket_channel_id.
    """
    tickets = client['TicketChannels'].find({'ATime': 'None'})
    return tickets


class TicketMessageView(discord.ui.View):
    """View for the message sent on top of every ticket."""

    def __init__(self):
        super().__init__(timeout=None)

        self.close_button = discord.ui.Button(style=discord.ButtonStyle.danger, label="Close Ticket",
                                              custom_id="close_ticket")
        self.add_item(self.close_button)
        self.close_button.callback = self.close_ticket

    async def close_ticket(self, interaction: discord.Interaction):
        self.disable_all_items()

        if not db_is_ticket_channel(interaction.guild.id, interaction.channel.id):
            await interaction.response.send_message("This is not a ticket channel.", ephemeral=True)
            return

        # Remove permissions from the ticket creator appropriately
        hide_time = get_setting(interaction.guild.id, "ticket_hide_time", "0")
        print('[Tickets] Auto hide time is', hide_time)
        if int(hide_time) > 0:
            print('[Tickets] Taking away send permissions')
            member = interaction.guild.get_member(db_get_ticket_creator(interaction.guild.id, interaction.channel.id))
            await interaction.channel.set_permissions(member, view_channel=True, read_messages=True, send_messages=False)
            db_archive_ticket(interaction.guild.id, interaction.channel.id)
        else:
            print('[Tickets] Taking away ALL permissions')
            member = interaction.guild.get_member(db_get_ticket_creator(interaction.guild.id, interaction.channel.id))
            await interaction.channel.set_permissions(member, view_channel=False, read_messages=False,
                                                      send_messages=False)
            db_remove_ticket_channel(interaction.guild.id, interaction.channel.id)

        # Send closed message
        await interaction.channel.send("Ticket closed by " + interaction.user.mention)

        await interaction.message.edit(view=self)
        await interaction.response.send_message("Ticket closed!", ephemeral=True)


class TicketCreateView(discord.ui.View):
    def __init__(self, button_label: str):
        super().__init__(timeout=None)

        self.button = discord.ui.Button(style=discord.ButtonStyle.primary, label=button_label,
                                        custom_id="create_ticket")
        self.add_item(self.button)
        self.button.callback = self.create_ticket

    async def create_ticket(self, interaction: discord.Interaction):
        category = interaction.guild.get_channel(int(get_setting(interaction.guild.id, "ticket_category", "0")))
        if category is None:
            await interaction.response.send_message(
                "A ticket category has to be set in order to create a ticket. Please ping the admins of the server to fix this.",
                ephemeral=True)
            return

        channel = await category.create_text_channel(f"ticket-{interaction.user.name}",
                                                     topic=f"Ticket for {interaction.user.display_name}",
                                                     reason="Ticket creation")

        # Set overwrite for the creator of the ticket, so they can see the channel and send messages
        await channel.set_permissions(interaction.user, read_messages=True, send_messages=True)

        # Send initial message
        await channel.send(
            "Ticket created by " + interaction.user.mention + "\n\nYou can use the buttons below to manage the ticket.",
            view=TicketMessageView())

        db_add_ticket_channel(interaction.guild.id, channel.id, interaction.user.id)

        await interaction.response.send_message("Ticket created! " + channel.mention, ephemeral=True)

        log_embed = discord.Embed(title="Ticket Created", description=f"Ticket created by {interaction.user.mention} in {channel.mention}")
        log_embed.add_field(name="Ticket ID", value=channel.id)
        log_embed.add_field(name="Ticket Creator", value=interaction.user.mention)
        log_embed.add_field(name="Ticket Channel", value=channel.mention)
        log_embed.add_field(name="Ticket Category", value=category.name)
        log_embed.add_field(name="Ticket Creation Time", value=get_now_for_server(interaction.guild.id).isoformat())

        await log_into_logs(interaction.guild, log_embed)


class Tickets(discord.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    tickets_commands = discord.SlashCommandGroup(name="tickets", description="Manage tickets")

    @discord.Cog.listener()
    async def on_ready(self):
        self.handle_hiding.start()
        self.handle_auto_archive.start()

    @discord.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        if not db_is_ticket_channel(message.guild.id, message.channel.id):
            return

        if db_is_archived(message.guild.id, message.channel.id):
            return

        db_update_mtime(message.guild.id, message.channel.id)

    @discord.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if after.author.bot:
            return

        if not db_is_ticket_channel(after.guild.id, after.channel.id):
            return

        db_update_mtime(after.guild.id, after.channel.id)

    @discord.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        if user.bot:
            return

        if not db_is_ticket_channel(reaction.message.guild.id, reaction.message.channel.id):
            return

        if db_is_archived(reaction.message.guild.id, reaction.message.channel.id):
            return

        db_update_mtime(reaction.message.guild.id, reaction.message.channel.id)

    @tickets_commands.command(name="send_message", description="Send a message that allows users to create a ticket")
    @discord.default_permissions(manage_guild=True)
    @commands.has_permissions(manage_guild=True)
    async def send_message(self, ctx: discord.ApplicationContext, message: str, button_label: str):
        if get_setting(ctx.guild.id, "ticket_category", "0") == "0":
            await ctx.respond("Please set a ticket category first!", ephemeral=True)
            return

        if not ctx.guild.get_channel(int(get_setting(ctx.guild.id, "ticket_category", "0"))):
            await ctx.respond("The ticket category has been deleted. Please set a new one.", ephemeral=True)
            return

        if not ctx.guild.me.guild_permissions.manage_channels or not ctx.guild.me.guild_permissions.manage_roles:
            await ctx.respond(
                "I need the Manage Channels (to create channels) and Manage Roles (to set permissions on ticket "
                "channels) permissions to create tickets.",
                ephemeral=True)
            return

        await ctx.channel.send(message, view=TicketCreateView(button_label))
        await ctx.respond("Message sent!", ephemeral=True)

        log_embed = discord.Embed(title="Ticket Message Sent", description=f"Ticket message sent by {ctx.user.mention} in {ctx.channel.mention}")
        log_embed.add_field(name="Ticket Message", value=message)
        log_embed.add_field(name="Ticket Message Button Label", value=button_label)
        log_embed.add_field(name="Ticket Message Channel", value=ctx.channel.mention)
        log_embed.add_field(name="Ticket Message Time", value=get_now_for_server(ctx.guild.id).isoformat())

        await log_into_logs(ctx.guild, log_embed)

    @tickets_commands.command(name="set_category",
                              description="Set the category where tickets will be created. Permissions will be copied "
                                          "from this category.")
    @discord.default_permissions(manage_guild=True)
    @commands.has_permissions(manage_guild=True)
    async def set_category(self, ctx: discord.ApplicationContext, category: discord.CategoryChannel):
        set_setting(ctx.guild.id, "ticket_category", str(category.id))
        await ctx.respond("Category set!", ephemeral=True)

        log_embed = discord.Embed(title="Ticket Category Set", description=f"Ticket category set by {ctx.user.mention} to {category.name}")
        log_embed.add_field(name="Ticket Category", value=category.name)
        log_embed.add_field(name="Ticket Category ID", value=category.id)
        log_embed.add_field(name="Ticket Category Time", value=get_now_for_server(ctx.guild.id).isoformat())

        await log_into_logs(ctx.guild, log_embed)

    @tickets_commands.command(name="set_hide_time",
                              description="Set the time that the ticket will be available for the creator after it's "
                                          "archived.")
    @discord.default_permissions(manage_guild=True)
    @commands.has_permissions(manage_guild=True)
    async def set_hide_time(self, ctx: discord.ApplicationContext, hours: int):
        set_setting(ctx.guild.id, "ticket_hide_time", str(hours))
        await ctx.respond("Hide time set!", ephemeral=True)

        log_embed = discord.Embed(title="Ticket Hide Time Set", description=f"Ticket hide time set by {ctx.user.mention} to {hours} hours")
        log_embed.add_field(name="Ticket Hide Time", value=hours)
        log_embed.add_field(name="Ticket Hide Time Time", value=get_now_for_server(ctx.guild.id).isoformat())

        await log_into_logs(ctx.guild, log_embed)

    @tickets_commands.command(name="set_archive_time",
                              description="Set the time that the ticket will be archived after no activity.")
    @discord.default_permissions(manage_guild=True)
    @commands.has_permissions(manage_guild=True)
    async def set_auto_archive_time(self, ctx: discord.ApplicationContext, hours: int):
        set_setting(ctx.guild.id, "ticket_archive_time", str(hours))
        await ctx.respond("Auto archive time set!", ephemeral=True)

        log_embed = discord.Embed(title="Ticket Archive Time Set", description=f"Ticket archive time set by {ctx.user.mention} to {hours} hours")
        log_embed.add_field(name="Ticket Archive Time", value=hours)
        log_embed.add_field(name="Ticket Archive Time Time", value=get_now_for_server(ctx.guild.id).isoformat())

        await log_into_logs(ctx.guild, log_embed)

    @tasks.loop(seconds=60)
    async def handle_hiding(self):
        for i in db_list_archived_tickets():
            guild = self.bot.get_guild(int(i['GuildID']))
            channel = guild.get_channel(int(i['TicketChannelID']))

            if guild is None or channel is None:
                return  # Skip if the guild or channel is not found

            if check_ticket_hide_time(i['GuildID'], i['TicketChannelID']):
                member = guild.get_member(db_get_ticket_creator(i['GuildID'], i['TicketChannelID']))
                await channel.set_permissions(member, read_messages=False, send_messages=False)
                db_remove_ticket_channel(i['GuildID'], i['TicketChannelID'])

                log_embed = discord.Embed(title="Ticket Hidden", description=f"Ticket hidden by the system in {channel.mention} because the hide time is up.")
                log_embed.add_field(name="Ticket Hidden Time", value=get_now_for_server(guild.id).isoformat())
                log_embed.add_field(name="Ticket Hidden Message", value=channel.jump_url)

                await log_into_logs(guild, log_embed)

    @tasks.loop(seconds=60)
    async def handle_auto_archive(self):
        # Ticket archiving after certain time of no changes
        for i in db_list_not_archived_tickets():
            if check_ticket_archive_time(i['GuildID'], i['TicketChannelID']):
                db_archive_ticket(i['GuildID'], i['TicketChannelID'])

                guild = self.bot.get_guild(int(i['GuildID']))
                channel = guild.get_channel(int(i['TicketChannelID']))

                # Remove permissions from the ticket creator appropriately
                atime = get_setting(guild.id, "ticket_hide_time", "0")
                if int(atime) > 0:
                    member = guild.get_member(
                        db_get_ticket_creator(guild.id, channel.id))
                    await channel.set_permissions(member, view_channel=True, read_messages=True,
                                                  send_messages=False)
                    db_archive_ticket(guild.id, channel.id)
                else:
                    member = guild.get_member(
                        db_get_ticket_creator(guild.id, channel.id))
                    await channel.set_permissions(member, view_channel=False, read_messages=False,
                                                  send_messages=False)
                    db_remove_ticket_channel(guild.id, channel.id)

                # Send closed message
                await channel.send(
                    "Ticket closed automatically because there was no activity for a certain amount of time.")

                log_embed = discord.Embed(title="Ticket Closed Automatically",
                                          description=f"Ticket closed automatically by the system in {channel.mention} because there was no activity for a certain amount of time.")
                log_embed.add_field(name="Ticket Closed Automatically Time", value=get_now_for_server(guild.id).isoformat())
                log_embed.add_field(name="Ticket Closed Automatically Message", value=channel.jump_url)

                await log_into_logs(guild, log_embed)
