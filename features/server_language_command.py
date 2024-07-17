import discord

from utils.settings import set_setting
from utils.languages import get_language_names, language_name_to_code, get_language_name
from utils.languages import get_translation_for_key_localized as trl


class ServerLanguageCommand(discord.Cog):

    @discord.slash_command(name='server_language', description="Change the server language.")
    @discord.option(name='lang', description="The language to set the server to.", choices=[get_language_names()])
    async def server_language(self, ctx: discord.ApplicationContext, lang: str):
        lang_code = language_name_to_code(lang)
        set_setting(ctx.guild.id, 'language', lang_code)
        await ctx.respond(trl(ctx.user.id, ctx.guild.id, "server_language_response").format(
            lang=get_language_name(lang_code, completeness=False)), ephemeral=True)
