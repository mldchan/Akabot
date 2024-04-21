import json

import discord

from utils.blocked import db_add_blocked_server, db_add_blocked_user, db_remove_blocked_server, db_remove_blocked_user

with open('config.json', 'r', encoding='utf8') as f:
    data = json.load(f)

ADMIN_GUILD = int(data["admin_guild"]) or 0
OWNER_ID = int(data["owner_id"]) or 0


class AdminCommands(discord.Cog):

    def __init__(self, bot: discord.Bot):
        super().__init__()
        self.bot = bot

    admin_subcommand = discord.SlashCommandGroup(name="admin", description="Manage the bot", guild_ids=[ADMIN_GUILD])

    blocklist_subcommand = admin_subcommand.create_subgroup(name="blocklist", description="Manage the blocklist",
        guild_ids=[ADMIN_GUILD])

    @blocklist_subcommand.command(name="add_user", description="Add a user to the blocklist", guild_ids=[ADMIN_GUILD])
    async def blocklist_add_user(self, ctx: discord.Interaction, user: discord.User, reason: str):
        if ctx.user.id != int(OWNER_ID):
            await ctx.response.send_message("You do not have permission", ephemeral=True)
            return
        db_add_blocked_user(user.id, reason)
        await ctx.response.send_message(f"User {user.mention} has been added to the blocklist", guild_ids=[ADMIN_GUILD])

    @blocklist_subcommand.command(name="remove_user", description="Remove a user from the blocklist")
    async def blocklist_remove_user(self, ctx: discord.Interaction, user: discord.User):
        if ctx.user.id != int(OWNER_ID):
            await ctx.response.send_message("You do not have permission", ephemeral=True)
            return
        db_remove_blocked_user(user.id)
        await ctx.response.send_message(f"User {user.mention} has been removed from the blocklist",
                                        guild_ids=[ADMIN_GUILD])

    @blocklist_subcommand.command(name="add_guild", description="Add a guild to the blocklist")
    async def blocklist_add_guild(self, ctx: discord.Interaction, guild: discord.Guild, reason: str):
        if ctx.user.id != int(OWNER_ID):
            await ctx.response.send_message("You do not have permission", ephemeral=True)
            return
        db_add_blocked_server(guild.id, reason)
        await ctx.response.send_message(f"Guild {guild.name} has been added to the blocklist", guild_ids=[ADMIN_GUILD])

    @blocklist_subcommand.command(name="remove_guild", description="Remove a guild from the blocklist")
    async def blocklist_remove_guild(self, ctx: discord.Interaction, guild: discord.Guild):
        if ctx.user.id != int(OWNER_ID):
            await ctx.response.send_message("You do not have permission", ephemeral=True)
            return
        db_remove_blocked_server(guild.id)
        await ctx.response.send_message(f"Guild {guild.name} has been removed from the blocklist")

    @admin_subcommand.command(name="servercount", description="How many servers is the bot in?")
    async def admin_servercount(self, ctx: discord.Interaction):
        servers = len(self.bot.guilds)
        channels = len([channel for channel in self.bot.get_all_channels()])
        members = len(set([member for member in self.bot.get_all_members()]))

        await ctx.response.send_message(f"""I am currently in {servers} guilds
-> {channels} total channels
-> {members} total members""", ephemeral=True)
