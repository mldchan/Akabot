import os

import discord
from utils.analytics import analytics

async def respond_to_help(ctx: discord.ApplicationContext, help_file: str):
    help_file = help_file.title().replace(" ", "-")
    file_info = os.stat(f"docs/{help_file}.md")
    if file_info.st_size > 2000:
        await ctx.respond(
            f"You can read about this feature [in the documentation](<https://github.com/Akatsuki2555/Akabot/wiki/{help_file}>), as it's too large to send on Discord.",
            ephemeral=True)
    else:
        with open(f"docs/{help_file}.md", "r") as f:
            content = f.read()
            await ctx.respond(content, ephemeral=True)


class Help(discord.Cog):
    def __init__(self, bot: discord.Bot):
        super().__init__()
        self.bot = bot

    help_group = discord.SlashCommandGroup(name='help', description='Help commands')

    @help_group.command(name="anti_raid", description="Help with Anti Raid feature")
    @analytics("help anti_raid")
    async def anti_raid(self, ctx: discord.ApplicationContext):
        await respond_to_help(ctx, "Anti Raid")

    @help_group.command(name="automod_actions", description="Help with Auto Role feature")
    @analytics("help automod_actions")
    async def automod_actions(self, ctx: discord.ApplicationContext):
        await respond_to_help(ctx, "Automod Actions")

    @help_group.command(name="chat_revive", description="Help with Chat Revive feature")
    @analytics("help chat_revive")
    async def chat_revive(self, ctx: discord.ApplicationContext):
        await respond_to_help(ctx, "Chat Revive")

    @help_group.command(name="chat_streaks", description="Help with Chat Streaks feature")
    @analytics("help chat_streaks")
    async def chat_streaks(self, ctx: discord.ApplicationContext):
        await respond_to_help(ctx, "Chat Streaks")

    @help_group.command(name="chat_summary", description="Help with Chat Summary feature")
    @analytics("help chat_summary")
    async def chat_summary(self, ctx: discord.ApplicationContext):
        await respond_to_help(ctx, "Chat Summary")

    @help_group.command(name="giveaways", description="Help with Giveaways feature")
    @analytics("help giveaways")
    async def giveaways(self, ctx: discord.ApplicationContext):
        await respond_to_help(ctx, "Giveaways")

    @help_group.command(name="leveling", description="Help with Leveling feature")
    @analytics("help leveling")
    async def leveling(self, ctx: discord.ApplicationContext):
        await respond_to_help(ctx, "Leveling")

    @help_group.command(name="logging", description="Help with Logging feature")
    @analytics("help logging")
    async def logging(self, ctx: discord.ApplicationContext):
        await respond_to_help(ctx, "Logging")

    @help_group.command(name="moderation", description="Help with Moderation feature")
    @analytics("help moderation")
    async def moderation(self, ctx: discord.ApplicationContext):
        await respond_to_help(ctx, "Moderation")

    @help_group.command(name="reaction_roles", description="Help with Reaction Roles feature")
    @analytics("help reaction_roles")
    async def reaction_roles(self, ctx: discord.ApplicationContext):
        await respond_to_help(ctx, "Reaction Roles")

    @help_group.command(name="verification", description="Help with Verification feature")
    @analytics("help verification")
    async def verification(self, ctx: discord.ApplicationContext):
        await respond_to_help(ctx, "Verification")

    @help_group.command(name="welcome_goodbye", description="Help with Welcome & Goodbye features")
    @analytics("help welcome_goodbye")
    async def welcome_goodbye(self, ctx: discord.ApplicationContext):
        await respond_to_help(ctx, "Welcome & Goodbye")
