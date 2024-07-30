import discord

from utils.config import get_key
# Let's say that trl is the short form of get_translation_for_key_localized across the codebase
from utils.languages import get_translation_for_key_localized as trl

ADMIN_GUILD = get_key("Admin_GuildID", "0")
OWNER_ID = get_key("Admin_OwnerID", "0")


class AdminCommands(discord.Cog):

    def __init__(self, bot: discord.Bot):
        super().__init__()
        self.bot = bot

    admin_subcommand = discord.SlashCommandGroup(name="admin", description="Manage the bot", guild_ids=[ADMIN_GUILD])

    @admin_subcommand.command(name="server_count", description="How many servers is the bot in?")
    async def admin_servercount(self, ctx: discord.ApplicationContext):
        servers = len(self.bot.guilds)
        channels = len([channel for channel in self.bot.get_all_channels()])
        members = len(set([member for member in self.bot.get_all_members()]))

        await ctx.respond(
            trl(ctx.user.id, ctx.guild.id, "bot_status_message").format(servers=str(servers), channels=str(channels),
                                                                        users=str(members)), ephemeral=True)
