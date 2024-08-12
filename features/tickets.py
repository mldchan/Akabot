import datetime

import discord
from discord.ext import commands, tasks

from database import conn
from utils.settings import set_setting, get_setting


def db_init():
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
    cur = conn.cursor()
    cur.execute(
        "create table if not exists tickets (id integer primary key autoincrement, guild_id bigint, ticket_channel_id "
        "bigint, user_id bigint, mtime text, atime text)")
    cur.close()
    conn.commit()


def db_add_ticket_channel(guild_id: int, ticket_category: int, user_id: int):
    cur = conn.cursor()
    cur.execute("insert into tickets(guild_id, ticket_channel_id, user_id, mtime, atime) values (?, ?, ?, ?, ?)",
                (guild_id, ticket_category, user_id, datetime.datetime.now().isoformat(), "None"))
    cur.close()
    conn.commit()


def db_is_ticket_channel(guild_id: int, ticket_channel_id: int):
    cur = conn.cursor()
    cur.execute("select * from tickets where guild_id = ? and ticket_channel_id = ?", (guild_id, ticket_channel_id))
    ticket = cur.fetchone()
    cur.close()
    return ticket is not None


def db_get_ticket_creator(guild_id: int, ticket_channel_id: int):
    cur = conn.cursor()
    cur.execute("select user_id from tickets where guild_id = ? and ticket_channel_id = ?",
                (guild_id, ticket_channel_id))
    user_id = cur.fetchone()
    cur.close()
    return user_id[0] if user_id is not None else None


def db_remove_ticket_channel(guild_id: int, ticket_channel_id: int):
    cur = conn.cursor()
    cur.execute("delete from tickets where guild_id = ? and ticket_channel_id = ?", (guild_id, ticket_channel_id))
    cur.close()
    conn.commit()


def db_update_mtime(guild_id: int, ticket_channel_id: int):
    cur = conn.cursor()
    cur.execute("update tickets set mtime = ? where guild_id = ? and ticket_channel_id = ?",
                (datetime.datetime.now().isoformat(), guild_id, ticket_channel_id))
    cur.close()
    conn.commit()


def check_ticket_archive_time(guild_id: int, ticket_channel_id: int) -> bool:
    archive_time = get_setting(guild_id, "ticket_archive_time", "0")  # hours
    if archive_time == "0":
        return False

    cur = conn.cursor()
    cur.execute("select mtime from tickets where guild_id = ? and ticket_channel_id = ?", (guild_id, ticket_channel_id))
    mtime = cur.fetchone()
    cur.close()

    if mtime is None:
        return False

    mtime = datetime.datetime.fromisoformat(mtime[0])
    if (datetime.datetime.now() - mtime).total_seconds() / 3600 >= int(archive_time):
        return True

    return False


def db_is_archived(guild_id: int, ticket_channel_id: int) -> bool:
    cur = conn.cursor()
    cur.execute("select atime from tickets where guild_id = ? and ticket_channel_id = ?", (guild_id, ticket_channel_id))
    atime = cur.fetchone()
    cur.close()

    return atime[0] != "None" if atime is not None else False


def check_ticket_hide_time(guild_id: int, ticket_channel_id: int) -> bool:
    if not db_is_archived(guild_id, ticket_channel_id):
        return False

    hide_time = get_setting(guild_id, "ticket_hide_time", "0")  # hours, hide time from archive
    if hide_time == "0":
        return False

    cur = conn.cursor()
    cur.execute("select atime from tickets where guild_id = ? and ticket_channel_id = ?", (guild_id, ticket_channel_id))
    atime = cur.fetchone()
    cur.close()

    if atime is None:
        return False

    atime = datetime.datetime.fromisoformat(atime[0])
    if (datetime.datetime.now() - atime).total_seconds() / 3600 >= int(hide_time):
        return True

    return False


def db_archive_ticket(guild_id: int, ticket_channel_id: int):
    cur = conn.cursor()
    cur.execute("update tickets set atime = ? where guild_id = ? and ticket_channel_id = ?",
                (datetime.datetime.now().isoformat(), guild_id, ticket_channel_id))
    cur.close()
    conn.commit()


def db_list_archived_tickets():
    """
    Get all archived tickets.
    :return: List of tuples with guild_id and ticket_channel_id.
    """
    cur = conn.cursor()
    cur.execute("select guild_id, ticket_channel_id from tickets where atime != 'None'")
    tickets = cur.fetchall()
    cur.close()
    return tickets


def db_list_not_archived_tickets():
    """
    Get all not archived tickets.
    :return: List of tuples with guild_id and ticket_channel_id.
    """
    cur = conn.cursor()
    cur.execute("select guild_id, ticket_channel_id from tickets where atime = 'None'")
    tickets = cur.fetchall()
    cur.close()
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
        atime = get_setting(interaction.guild.id, "ticket_hide_time", "0")
        if atime == "0":
            member = interaction.guild.get_member(db_get_ticket_creator(interaction.guild.id, interaction.channel.id))
            await interaction.channel.set_permissions(member, view_channel=False, read_messages=False,
                                                      send_messages=False)
            db_remove_ticket_channel(interaction.guild.id, interaction.channel.id)
        else:
            member = interaction.guild.get_member(db_get_ticket_creator(interaction.guild.id, interaction.channel.id))
            await interaction.channel.set_permissions(member, view_channel=False, read_messages=True,
                                                      send_messages=False)
            db_archive_ticket(interaction.guild.id, interaction.channel.id)

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


class Tickets(discord.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        db_init()

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

    @tickets_commands.command(name="set_category",
                              description="Set the category where tickets will be created. Permissions will be copied "
                                          "from this category.")
    @discord.default_permissions(manage_guild=True)
    @commands.has_permissions(manage_guild=True)
    async def set_category(self, ctx: discord.ApplicationContext, category: discord.CategoryChannel):
        set_setting(ctx.guild.id, "ticket_category", str(category.id))
        await ctx.respond("Category set!", ephemeral=True)

    @tickets_commands.command(name="set_hide_time",
                              description="Set the time that the ticket will be available for the creator after it's "
                                          "archived.")
    @discord.default_permissions(manage_guild=True)
    @commands.has_permissions(manage_guild=True)
    async def set_hide_time(self, ctx: discord.ApplicationContext, hours: int):
        set_setting(ctx.guild.id, "ticket_hide_time", str(hours))
        await ctx.respond("Hide time set!", ephemeral=True)

    @tickets_commands.command(name="set_archive_time",
                              description="Set the time that the ticket will be archived after no activity.")
    @discord.default_permissions(manage_guild=True)
    @commands.has_permissions(manage_guild=True)
    async def set_auto_archive_time(self, ctx: discord.ApplicationContext, hours: int):
        set_setting(ctx.guild.id, "ticket_archive_time", str(hours))
        await ctx.respond("Auto archive time set!", ephemeral=True)

    @tasks.loop(seconds=60)
    async def handle_hiding(self):
        for i in db_list_archived_tickets():
            guild = self.bot.get_guild(i[0])
            channel = guild.get_channel(i[1])

            if check_ticket_hide_time(i[0], i[1]):
                member = guild.get_member(db_get_ticket_creator(i[0], i[1]))
                await channel.set_permissions(member, read_messages=False, send_messages=False)
                db_remove_ticket_channel(i[0], i[1])

    @tasks.loop(seconds=60)
    async def handle_auto_archive(self):
        # Ticket archiving after certain time of no changes
        for i in db_list_not_archived_tickets():
            if check_ticket_archive_time(i[0], i[1]):
                db_archive_ticket(i[0], i[1])

                guild = self.bot.get_guild(i[0])
                channel = guild.get_channel(i[1])

                # Remove permissions from the ticket creator appropriately
                atime = get_setting(guild.id, "ticket_hide_time", "0")
                if atime == "0":
                    member = guild.get_member(
                        db_get_ticket_creator(guild.id, channel.id))
                    await channel.set_permissions(member, view_channel=False, read_messages=False,
                                                  send_messages=False)
                    db_remove_ticket_channel(guild.id, channel.id)
                else:
                    member = guild.get_member(
                        db_get_ticket_creator(guild.id, channel.id))
                    await channel.set_permissions(member, view_channel=True, read_messages=True,
                                                  send_messages=False)
                    db_archive_ticket(guild.id, channel.id)

                # Send closed message
                await channel.send(
                    "Ticket closed automatically because there was no activity for a certain amount of time.")
