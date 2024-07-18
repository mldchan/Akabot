import discord

from utils.languages import get_language_names, language_name_to_code, get_language_name
from utils.languages import get_translation_for_key_localized as trl
from utils.per_user_settings import set_per_user_setting, db_init


class PerUserSettings(discord.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        db_init()

    user_settings_group = discord.SlashCommandGroup(name='user_settings', description='Per user settings')

    @user_settings_group.command(name='chat_streaks_alerts', description='Enable or disable chat streaks alerts')
    @discord.option(name='state', description='How notifications should be sent',
                    choices=['enabled', 'only when lost', 'off'])
    async def chat_streaks_alerts(self, ctx: discord.ApplicationContext, state: str):
        set_per_user_setting(ctx.user.id, 'chat_streaks_alerts', state)
        if state == 'enabled':
            state = trl(ctx.user.id, ctx.guild.id, "per_user_chat_streak_state_enabled")
        elif state == 'only when lost':
            state = trl(ctx.user.id, ctx.guild.id, "per_user_chat_streak_state_only_when_lost")
        else:
            state = trl(ctx.user.id, ctx.guild.id, "per_user_chat_streak_state_disabled")
        await ctx.respond(trl(ctx.user.id, ctx.guild.id, "per_user_chat_streak_response").format(state=state),
                          ephemeral=True)

    @user_settings_group.command(name='langauge',
                                 description='Set your personal language, applies across servers for you')
    @discord.option(name='lang', description='Your language', choices=get_language_names())
    async def set_language(self, ctx: discord.ApplicationContext, lang: str):
        lang_code = language_name_to_code(lang)

        set_per_user_setting(ctx.user.id, 'language', lang_code)
        await ctx.respond(trl(ctx.user.id, ctx.guild.id, "per_user_language_set").format(
            lang=get_language_name(lang_code, completeness=False)),
            ephemeral=True)
