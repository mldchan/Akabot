import discord

from utils.blocked import db_add_blocked_server, db_add_blocked_user, db_remove_blocked_server, db_remove_blocked_user
from utils.config import get_key

ADMIN_GUILD = get_key("Admin_GuildID", "0")
OWNER_ID = get_key("Admin_OwnerID", "0")


class AdminCommands(discord.Cog):

    def __init__(self, bot: discord.Bot):
        super().__init__()
        self.bot = bot

    admin_subcommand = discord.SlashCommandGroup(name="admin", description="Manage the bot", guild_ids=[ADMIN_GUILD])

    blocklist_subcommand = admin_subcommand.create_subgroup(name="blocklist", description="Manage the blocklist",
        guild_ids=[ADMIN_GUILD])

    @blocklist_subcommand.command(name="add_user", description="Add a user to the blocklist", guild_ids=[ADMIN_GUILD])
    async def blocklist_add_user(self, ctx: discord.ApplicationContext, user: discord.User, reason: str):
        if ctx.user.id != int(OWNER_ID):
            await ctx.respond("You do not have permission", ephemeral=True)
            return
        db_add_blocked_user(user.id, reason)
        await ctx.respond(f"User {user.mention} has been added to the blocklist", guild_ids=[ADMIN_GUILD])

    @blocklist_subcommand.command(name="remove_user", description="Remove a user from the blocklist")
    async def blocklist_remove_user(self, ctx: discord.ApplicationContext, user: discord.User):
        if ctx.user.id != int(OWNER_ID):
            await ctx.respond("You do not have permission", ephemeral=True)
            return
        db_remove_blocked_user(user.id)
        await ctx.respond(f"User {user.mention} has been removed from the blocklist",
                                        guild_ids=[ADMIN_GUILD])

    @blocklist_subcommand.command(name="add_guild", description="Add a guild to the blocklist")
    async def blocklist_add_guild(self, ctx: discord.ApplicationContext, guild: discord.Guild, reason: str):
        if ctx.user.id != int(OWNER_ID):
            await ctx.respond("You do not have permission", ephemeral=True)
            return
        db_add_blocked_server(guild.id, reason)
        await ctx.respond(f"Guild {guild.name} has been added to the blocklist", guild_ids=[ADMIN_GUILD])

    @blocklist_subcommand.command(name="remove_guild", description="Remove a guild from the blocklist")
    async def blocklist_remove_guild(self, ctx: discord.ApplicationContext, guild: discord.Guild):
        if ctx.user.id != int(OWNER_ID):
            await ctx.respond("You do not have permission", ephemeral=True)
            return
        db_remove_blocked_server(guild.id)
        await ctx.respond(f"Guild {guild.name} has been removed from the blocklist")

    @admin_subcommand.command(name="servercount", description="How many servers is the bot in?")
    async def admin_servercount(self, ctx: discord.ApplicationContext):
        servers = len(self.bot.guilds)
        channels = len([channel for channel in self.bot.get_all_channels()])
        members = len(set([member for member in self.bot.get_all_members()]))

        await ctx.respond(f"""I am currently in {servers} guilds
-> {channels} total channels
-> {members} total members""", ephemeral=True)
        
    @admin_subcommand.command(name='test_error', description='Test the error handler')
    async def test_error(self, ctx: discord.ApplicationContext):
        await ctx.respond("The bot will throw an error NOW!", ephemeral=True)
        raise Exception("Testing error")
