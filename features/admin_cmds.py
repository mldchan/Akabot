
import discord
from utils.blocked import db_add_blocked_server, db_add_blocked_user, db_remove_blocked_server, db_remove_blocked_user


class AdminCommands(discord.Cog):

    def __init__(self, bot: discord.Bot):
        super().__init__()
        self.bot = bot

    admin_subcommand = discord.SlashCommandGroup(
        name="admin", description="Manage the bot")  # TODO: Make available only in development guild

    blocklist_subcommand = discord.SlashCommandGroup(
        name="blocklist", description="Manage the blocklist", parent=admin_subcommand)

    @blocklist_subcommand.command(name="add_user", description="Add a user to the blocklist")
    async def blocklist_add_user(self, ctx: discord.Interaction, user: discord.User):
        # TODO: Implement the blocklist add user function
        pass

    @blocklist_subcommand.command(name="remove_user", description="Remove a user from the blocklist")
    async def blocklist_remove_user(self, ctx: discord.Interaction, user: discord.User):
        # TODO: Implement the blocklist remove user function
        pass

    @blocklist_subcommand.command(name="add_guild", description="Add a guild to the blocklist")
    async def blocklist_add_guild(self, ctx: discord.Interaction, guild: discord.Guild):
        # TODO: Implement the blocklist add guild function
        pass

    @blocklist_subcommand.command(name="remove_guild", description="Remove a guild from the blocklist")
    async def blocklist_remove_guild(self, ctx: discord.Interaction, guild: discord.Guild):
        # TODO: Implement the blocklist remove guild function
        pass
