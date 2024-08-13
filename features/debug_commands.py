import discord

from utils.tzutil import get_now_for_server


class DebugCommands(discord.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    dev_commands_group = discord.SlashCommandGroup(name="dev_commands", description="Developer commands")

    @dev_commands_group.command(name="ping", description="Get ping to Discord API")
    async def ping(self, ctx: discord.ApplicationContext):
        await ctx.respond(f"Pong! {round(self.bot.latency * 1000)}ms", ephemeral=True)

    @dev_commands_group.command(name="now", description="Get now for server")
    async def now(self, ctx: discord.ApplicationContext):
        await ctx.respond(f"Current time: {get_now_for_server(ctx.guild.id).isoformat()}", ephemeral=True)
