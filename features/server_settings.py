import re

import discord

from utils.analytics import analytics
from utils.languages import get_translation_for_key_localized as trl
from utils.languages import language_name_to_code, get_language_names, get_language_name
from utils.settings import set_setting


class ServerSettings(discord.Cog):
    server_settings_group = discord.SlashCommandGroup(name='server_settings', description='Server settings')

    @server_settings_group.command(name='language', description="Change the server language.")
    @discord.option(name='lang', description="The language to set the server to.", choices=get_language_names())
    @analytics("server_settings language")
    async def server_language(self, ctx: discord.ApplicationContext, lang: str):
        lang_code = language_name_to_code(lang)
        await set_setting(ctx.guild.id, 'language', lang_code)
        await ctx.respond((await trl(ctx.user.id, ctx.guild.id, "server_language_response", append_tip=True)).format(
            lang=get_language_name(lang_code, completeness=False)), ephemeral=True)

    @server_settings_group.command(name='tz', description='Timezone setting')
    @discord.option(name='tz', description='Timezone')
    @analytics("server_settings timezone")
    async def tz_setting(self, ctx: discord.ApplicationContext, tz: float):
        if not re.match(r"^[+-]?\d+(\.\d)?$", str(tz)):
            await ctx.respond(await trl(ctx.user.id, ctx.guild.id, "server_tz_invalid"), ephemeral=True)
            return

        # check range
        if tz > 14 or tz < -12:
            await ctx.respond(await trl(ctx.user.id, ctx.guild.id, "server_tz_invalid"), ephemeral=True)
            return

        await set_setting(ctx.guild.id, 'timezone_offset', str(tz))

        tz_formatted = str(tz)
        if re.match(r'^[+-]?\d+\.0$', tz_formatted):
            tz_formatted = tz_formatted[:-2]
        await ctx.respond((await trl(ctx.user.id, ctx.guild.id, "server_tz_response", append_tip=True)).format(tz=tz_formatted), ephemeral=True)
