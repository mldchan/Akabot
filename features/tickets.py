import discord
from discord.ext import commands

from database import conn
from utils.settings import set_setting, get_setting


def db_init():
    cur = conn.cursor()
    cur.execute(
        "create table if not exists tickets (id integer primary key autoincrement, guild_id bigint, ticket_channel_id "
        "bigint, user_id bigint)")
    cur.close()
    conn.commit()


def db_add_ticket_channel(guild_id: int, ticket_category: int, user_id: int):
    cur = conn.cursor()
    cur.execute("insert into tickets(guild_id, ticket_channel_id, user_id) values (?, ?, ?)",
                (guild_id, ticket_category, user_id))
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

        # Remove user from ticket
        member = interaction.guild.get_member(db_get_ticket_creator(interaction.guild.id, interaction.channel.id))
        await interaction.channel.set_permissions(member, read_messages=False, send_messages=False)

        # Send closed message
        await interaction.channel.send("Ticket closed by " + interaction.user.mention)

        # Delete ticket from database
        db_remove_ticket_channel(interaction.guild.id, interaction.channel.id)

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
