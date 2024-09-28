import datetime

import discord
from discord.ext import commands, tasks

from database import get_conn
from utils.settings import set_setting, get_setting
from utils.tzutil import get_now_for_server
from utils.logging_util import log_into_logs


async def db_init():
    """
    Initialize the database for the tickets feature.
    id is the primary key and autoincrements.
    guild_id is the Guild ID.
    ticket_channel_id is the Ticket Channel ID.
    user_id is the User ID of the ticket creator.
    mtime is the last modification time of the ticket. This includes messages and reactions.
    atime is the time the ticket was archived. Used for letting the user see the ticket for a certain amount of time.
    atime is set to "None" (string) if the ticket is not archived.
    """
    db = await get_conn()
    await db.execute(
        "create table if not exists tickets (id integer primary key autoincrement, guild_id bigint, ticket_channel_id "
        "bigint, user_id bigint, mtime text, atime text)")
    await db.commit()
    await db.close()


async def db_add_ticket_channel(guild_id: int, ticket_category: int, user_id: int):
    db = await get_conn()
    await db.execute("insert into tickets(guild_id, ticket_channel_id, user_id, mtime, atime) values (?, ?, ?, ?, ?)",
                (guild_id, ticket_category, user_id, get_now_for_server(guild_id).isoformat(), "None"))
    await db.commit()
    await db.close()


async def db_is_ticket_channel(guild_id: int, ticket_channel_id: int):
    db = await get_conn()
    cur = await db.execute("select * from tickets where guild_id = ? and ticket_channel_id = ?", (guild_id, ticket_channel_id))
    ticket = await cur.fetchone()
    await db.close()
    return ticket is not None


async def db_get_ticket_creator(guild_id: int, ticket_channel_id: int):
    db = await get_conn()
    cur = await db.execute("select user_id from tickets where guild_id = ? and ticket_channel_id = ?",
                (guild_id, ticket_channel_id))
    user_id = await cur.fetchone()
    await db.close()
    return user_id[0] if user_id is not None else None


async def db_remove_ticket_channel(guild_id: int, ticket_channel_id: int):
    db = await get_conn()
    await db.execute("delete from tickets where guild_id = ? and ticket_channel_id = ?", (guild_id, ticket_channel_id))
    await db.commit()
    await db.close()


async def db_update_mtime(guild_id: int, ticket_channel_id: int):
    db = await get_conn()
    await db.execute("update tickets set mtime = ? where guild_id = ? and ticket_channel_id = ?",
                     ((await get_now_for_server(guild_id)).isoformat(), guild_id, ticket_channel_id))
    await db.commit()
    await db.close()


async def check_ticket_archive_time(guild_id: int, ticket_channel_id: int) -> bool:
    archive_time = await get_setting(guild_id, "ticket_archive_time", "0")  # hours
    if archive_time == "0":
        return False

    db = await get_conn()
    cur = await db.execute("select mtime from tickets where guild_id = ? and ticket_channel_id = ?", (guild_id, ticket_channel_id))
    mtime = await cur.fetchone()
    await db.close()

    if mtime is None:
        return False

    mtime = datetime.datetime.fromisoformat(mtime[0])
    if (await get_now_for_server(guild_id) - mtime).total_seconds() / 3600 >= int(archive_time):
        return True

    return False


async def db_is_archived(guild_id: int, ticket_channel_id: int) -> bool:
    db = await get_conn()
    cur = await db.execute("select atime from tickets where guild_id = ? and ticket_channel_id = ?", (guild_id, ticket_channel_id))
    atime = await cur.fetchone()
    await db.close()

    return atime[0] != "None" if atime is not None else False


async def check_ticket_hide_time(guild_id: int, ticket_channel_id: int) -> bool:
    if not await db_is_archived(guild_id, ticket_channel_id):
        return False

    hide_time = await get_setting(guild_id, "ticket_hide_time", "0")  # hours, hide time from archive
    if hide_time == "0":
        return False

    db = await get_conn()
    cur = await db.execute("select atime from tickets where guild_id = ? and ticket_channel_id = ?", (guild_id, ticket_channel_id))
    atime = await cur.fetchone()
    await db.close()

    if atime is None:
        return False

    atime = datetime.datetime.fromisoformat(atime[0])
    if (await get_now_for_server(guild_id) - atime).total_seconds() / 3600 >= int(hide_time):
        return True

    return False


async def db_archive_ticket(guild_id: int, ticket_channel_id: int):
    db = await get_conn()
    await db.execute("update tickets set atime = ? where guild_id = ? and ticket_channel_id = ?",
                     ((await get_now_for_server(guild_id)).isoformat(), guild_id, ticket_channel_id))
    await db.commit()
    await db.close()


async def db_list_archived_tickets():
    """
    Get all archived tickets.
    :return: List of tuples with guild_id and ticket_channel_id.
    """
    db = await get_conn()
    cur = await db.execute("select guild_id, ticket_channel_id from tickets where atime != 'None'")
    tickets = await cur.fetchall()
    await db.close()
    return tickets


async def db_list_not_archived_tickets():
    """
    Get all not archived tickets.
    :return: List of tuples with guild_id and ticket_channel_id.
    """
    db = await get_conn()
    cur = await db.execute("select guild_id, ticket_channel_id from tickets where atime = 'None'")
    tickets = await cur.fetchall()
    await db.close()
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

        if not await db_is_ticket_channel(interaction.guild.id, interaction.channel.id):
            await interaction.response.send_message("This is not a ticket channel.", ephemeral=True)
            return

        # Remove permissions from the ticket creator appropriately
        atime = await get_setting(interaction.guild.id, "ticket_hide_time", "0")
        if atime == "0":
            member = interaction.guild.get_member(await db_get_ticket_creator(interaction.guild.id, interaction.channel.id))
            await interaction.channel.set_permissions(member, view_channel=False, read_messages=False,
                                                      send_messages=False)
            await db_remove_ticket_channel(interaction.guild.id, interaction.channel.id)
        else:
            member = interaction.guild.get_member(await db_get_ticket_creator(interaction.guild.id, interaction.channel.id))
            await interaction.channel.set_permissions(member, view_channel=False, read_messages=True,
                                                      send_messages=False)
            await db_archive_ticket(interaction.guild.id, interaction.channel.id)

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
        category = interaction.guild.get_channel(int(await get_setting(interaction.guild.id, "ticket_category", "0")))
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

        await db_add_ticket_channel(interaction.guild.id, channel.id, interaction.user.id)

        await interaction.response.send_message("Ticket created! " + channel.mention, ephemeral=True)

        log_embed = discord.Embed(title="Ticket Created", description=f"Ticket created by {interaction.user.mention} in {channel.mention}")
        log_embed.add_field(name="Ticket ID", value=channel.id)
        log_embed.add_field(name="Ticket Creator", value=interaction.user.mention)
        log_embed.add_field(name="Ticket Channel", value=channel.mention)
        log_embed.add_field(name="Ticket Category", value=category.name)
        log_embed.add_field(name="Ticket Creation Time", value=(await get_now_for_server(interaction.guild.id)).isoformat())
        log_embed.add_field(name="Ticket Message", value=interaction.message.jump_url)

        await log_into_logs(interaction.guild, log_embed)


class Tickets(discord.Cog):
    def __init__(self, bot: discord.Bot):
        bot.loop.create_task(db_init())
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

        if not await db_is_ticket_channel(message.guild.id, message.channel.id):
            return

        if await db_is_archived(message.guild.id, message.channel.id):
            return

        await db_update_mtime(message.guild.id, message.channel.id)

    @discord.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if after.author.bot:
            return

        if not await db_is_ticket_channel(after.guild.id, after.channel.id):
            return

        await db_update_mtime(after.guild.id, after.channel.id)

    @discord.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        if user.bot:
            return

        if not await db_is_ticket_channel(reaction.message.guild.id, reaction.message.channel.id):
            return

        if await db_is_archived(reaction.message.guild.id, reaction.message.channel.id):
            return

        await db_update_mtime(reaction.message.guild.id, reaction.message.channel.id)

    @tickets_commands.command(name="send_message", description="Send a message that allows users to create a ticket")
    @discord.default_permissions(manage_guild=True)
    @commands.has_permissions(manage_guild=True)
    async def send_message(self, ctx: discord.ApplicationContext, message: str, button_label: str):
        if await get_setting(ctx.guild.id, "ticket_category", "0") == "0":
            await ctx.respond("Please set a ticket category first!", ephemeral=True)
            return

        if not ctx.guild.get_channel(int(await get_setting(ctx.guild.id, "ticket_category", "0"))):
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
        log_embed.add_field(name="Ticket Message Message", value=ctx.message.jump_url)

        await log_into_logs(ctx.guild, log_embed)

    @tickets_commands.command(name="set_category",
                              description="Set the category where tickets will be created. Permissions will be copied "
                                          "from this category.")
    @discord.default_permissions(manage_guild=True)
    @commands.has_permissions(manage_guild=True)
    async def set_category(self, ctx: discord.ApplicationContext, category: discord.CategoryChannel):
        await set_setting(ctx.guild.id, "ticket_category", str(category.id))
        await ctx.respond("Category set!", ephemeral=True)

        log_embed = discord.Embed(title="Ticket Category Set", description=f"Ticket category set by {ctx.user.mention} to {category.name}")
        log_embed.add_field(name="Ticket Category", value=category.name)
        log_embed.add_field(name="Ticket Category ID", value=category.id)
        log_embed.add_field(name="Ticket Category Time", value=get_now_for_server(ctx.guild.id).isoformat())
        log_embed.add_field(name="Ticket Category Message", value=ctx.message.jump_url)

        await log_into_logs(ctx.guild, log_embed)

    @tickets_commands.command(name="set_hide_time",
                              description="Set the time that the ticket will be available for the creator after it's "
                                          "archived.")
    @discord.default_permissions(manage_guild=True)
    @commands.has_permissions(manage_guild=True)
    async def set_hide_time(self, ctx: discord.ApplicationContext, hours: int):
        await set_setting(ctx.guild.id, "ticket_hide_time", str(hours))
        await ctx.respond("Hide time set!", ephemeral=True)

        log_embed = discord.Embed(title="Ticket Hide Time Set", description=f"Ticket hide time set by {ctx.user.mention} to {hours} hours")
        log_embed.add_field(name="Ticket Hide Time", value=hours)
        log_embed.add_field(name="Ticket Hide Time Time", value=get_now_for_server(ctx.guild.id).isoformat())
        log_embed.add_field(name="Ticket Hide Time Message", value=ctx.message.jump_url)

        await log_into_logs(ctx.guild, log_embed)

    @tickets_commands.command(name="set_archive_time",
                              description="Set the time that the ticket will be archived after no activity.")
    @discord.default_permissions(manage_guild=True)
    @commands.has_permissions(manage_guild=True)
    async def set_auto_archive_time(self, ctx: discord.ApplicationContext, hours: int):
        await set_setting(ctx.guild.id, "ticket_archive_time", str(hours))
        await ctx.respond("Auto archive time set!", ephemeral=True)

        log_embed = discord.Embed(title="Ticket Archive Time Set", description=f"Ticket archive time set by {ctx.user.mention} to {hours} hours")
        log_embed.add_field(name="Ticket Archive Time", value=hours)
        log_embed.add_field(name="Ticket Archive Time Time", value=get_now_for_server(ctx.guild.id).isoformat())
        log_embed.add_field(name="Ticket Archive Time Message", value=ctx.message.jump_url)

        await log_into_logs(ctx.guild, log_embed)

    @tasks.loop(seconds=60)
    async def handle_hiding(self):
        for i in await db_list_archived_tickets():
            guild = self.bot.get_guild(i[0])
            channel = guild.get_channel(i[1])

            if await check_ticket_hide_time(i[0], i[1]):
                member = guild.get_member(await db_get_ticket_creator(i[0], i[1]))
                await channel.set_permissions(member, read_messages=False, send_messages=False)
                await db_remove_ticket_channel(i[0], i[1])

                log_embed = discord.Embed(title="Ticket Hidden", description=f"Ticket hidden by the system in {channel.mention} because the hide time is up.")
                log_embed.add_field(name="Ticket Hidden Time", value=get_now_for_server(guild.id).isoformat())
                log_embed.add_field(name="Ticket Hidden Message", value=channel.jump_url)

                await log_into_logs(guild, log_embed)

    @tasks.loop(seconds=60)
    async def handle_auto_archive(self):
        # Ticket archiving after certain time of no changes
        for i in await db_list_not_archived_tickets():
            if await check_ticket_archive_time(i[0], i[1]):
                await db_archive_ticket(i[0], i[1])

                guild = self.bot.get_guild(i[0])
                channel = guild.get_channel(i[1])

                # Remove permissions from the ticket creator appropriately
                atime = await get_setting(guild.id, "ticket_hide_time", "0")
                if atime == "0":
                    member = guild.get_member(
                        await db_get_ticket_creator(guild.id, channel.id))
                    await channel.set_permissions(member, view_channel=False, read_messages=False,
                                                  send_messages=False)
                    await db_remove_ticket_channel(guild.id, channel.id)
                else:
                    member = guild.get_member(
                        await db_get_ticket_creator(guild.id, channel.id))
                    await channel.set_permissions(member, view_channel=True, read_messages=True,
                                                  send_messages=False)
                    await db_archive_ticket(guild.id, channel.id)

                # Send closed message
                await channel.send(
                    "Ticket closed automatically because there was no activity for a certain amount of time.")

                log_embed = discord.Embed(title="Ticket Closed Automatically", description=f"Ticket closed automatically by the system in {channel.mention} because there was no activity for a certain amount of time.")
                log_embed.add_field(name="Ticket Closed Automatically Time", value=(await get_now_for_server(guild.id)).isoformat())
                log_embed.add_field(name="Ticket Closed Automatically Message", value=channel.jump_url)

                await log_into_logs(guild, log_embed)
