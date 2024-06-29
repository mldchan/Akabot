import discord

from utils.settings import get_setting, set_setting
from utils.logging import log_into_logs
from discord.ext import commands
from utils.blocked import is_blocked

class VelkyStompies(discord.Cog):
    @discord.slash_command(name="stompies", description="Velky's stompies command")
    async def velky_stompies(self, ctx: discord.ApplicationContext):
        if get_setting(ctx.guild.id, "stompies_enabled", "True") == "False":
            await ctx.respond("The command is disabled", ephemeral=True)
            return

        await ctx.respond("https://tenor.com/view/stompies-velky-cute-angwy-gif-13012534518393437613")

    stompies_settings_group = discord.SlashCommandGroup("stompies_settings", "Stompies commands")

    @stompies_settings_group.command(name="enable", description="Set the enabled state of the Velky Stompies command")
    @discord.option(name="enabled", description="Whether the Velky stompies command is enabled", type=bool)
    @discord.default_permissions(manage_guild=True)
    @is_blocked()
    async def stompies_enable(self, ctx: discord.ApplicationContext, enabled: bool):
        old_value = get_setting(ctx.guild.id, "stompies_enabled", str(enabled)) == "True"

        if old_value != enabled:
            logging_embed = discord.Embed(title="Stompies enabled changed")
            logging_embed.add_field(name="User", value=f"{ctx.user.mention}")
            logging_embed.add_field(name="Value", value=f'{"Enabled" if old_value else "Disabled"} -> {"Enabled" if enabled else "Disabled"}')

            await log_into_logs(ctx.guild, logging_embed)

        set_setting(ctx.guild.id, 'stompies_enabled', str(enabled))

        await ctx.respond(f'Succcessfully turned on stompies' if enabled else 'Successfully turned off stompies', ephemeral=True)
