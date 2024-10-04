import datetime

import discord

from database import client
from utils.analytics import analytics
from utils.languages import get_language_names, language_name_to_code, get_language_name
from utils.languages import get_translation_for_key_localized as trl
from utils.per_user_settings import set_per_user_setting, get_per_user_setting, unset_per_user_setting


def days_in_month(month: int, year: int):
    if month == 2:
        return 29 if year % 4 == 0 and year % 100 != 0 else 28

    if month in [1, 3, 5, 7, 8, 10, 12]:
        return 31
    else:
        return 30


class PerUserSettings(discord.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    user_settings_group = discord.SlashCommandGroup(name='user_settings', description='Per user settings')

    @user_settings_group.command(name='chat_streaks_alerts', description='Enable or disable chat streaks alerts')
    @discord.option(name='state', description='How notifications should be sent', choices=['enabled', 'only when lost', 'off'])
    @analytics("user_settings chat_streaks_alerts")
    async def chat_streaks_alerts(self, ctx: discord.ApplicationContext, state: str):
        set_per_user_setting(ctx.user.id, 'chat_streaks_alerts', state)
        if state == 'enabled':
            state = trl(ctx.user.id, ctx.guild.id, "per_user_chat_streak_state_enabled")
        elif state == 'only when lost':
            state = trl(ctx.user.id, ctx.guild.id, "per_user_chat_streak_state_only_when_lost")
        else:
            state = trl(ctx.user.id, ctx.guild.id, "per_user_chat_streak_state_disabled")
        await ctx.respond(trl(ctx.user.id, ctx.guild.id, "per_user_chat_streak_response", append_tip=True).format(state=state),
                          ephemeral=True)

    @user_settings_group.command(name='langauge', description='Set your personal language, applies across servers for you')
    @discord.option(name='lang', description='Your language', choices=get_language_names())
    @analytics("user_settings language")
    async def set_language(self, ctx: discord.ApplicationContext, lang: str):
        lang_code = language_name_to_code(lang)

        set_per_user_setting(ctx.user.id, 'language', lang_code)
        await ctx.respond(trl(ctx.user.id, ctx.guild.id, "per_user_language_set", append_tip=True).format(
            lang=get_language_name(lang_code, completeness=False)), ephemeral=True)

    @user_settings_group.command(name='birthday', description='Set your birthday for Birthday Announcements.')
    @discord.option(name='birthday', description='Your birthday in the format YYYY-MM-DD')
    @analytics("user_settings birthday")
    async def set_birthdate(self, ctx: discord.ApplicationContext, year: int, month: int, day: int):
        now = datetime.datetime.now()
        if now.year - 100 < year < now.year - 13:
            await ctx.respond(trl(ctx.user.id, ctx.guild.id, 'birthday_invalid_year'), ephemeral=True)
            return

        if 1 <= month <= 12:
            await ctx.respond(trl(ctx.user.id, ctx.guild.id, 'birthday_invalid_month'), ephemeral=True)
            return

        if 1 <= day <= days_in_month(month, year):
            await ctx.respond(trl(ctx.user.id, ctx.guild.id, 'birthday_invalid_day'), ephemeral=True)
            return

        client['UserBirthday'].update_one({'UserID': ctx.author.id}, {'$set': {'Birth.Year': year, 'Birth.Month': month, 'Birth.Day': day}}, upsert=True)
        await ctx.respond(trl(ctx.user.id, ctx.guild.id, 'birthday_set'), ephemeral=True)

    @user_settings_group.command(name="birthday_settings", description="Personalize your birthday settings")
    @discord.option(name="send_dm", type=bool, description="Whether to allow this bot to send DMs to you")
    @analytics("user_settings birthday_settings")
    async def set_birthday_settings(self, ctx: discord.ApplicationContext, send_dm: bool | None = None):
        if send_dm is not None:
            set_per_user_setting(ctx.user.id, 'birthday_send_dm', str(send_dm).lower())

        send_dm = get_per_user_setting(ctx.user.id, 'birthday_send_dm', "false")

        send_dm = trl(ctx.user.id, ctx.guild.id, "per_user_birthday_send_dm_enabled", append_tip=True) \
            if send_dm else trl(ctx.user.id, ctx.guild.id, "per_user_birthday_send_dm_disabled", append_tip=True)

        await ctx.respond(f"{send_dm}", ephemeral=True)

    @user_settings_group.command(name="birthday_announcements", description="Whether to announce birthdays in the server you're currently in")
    @discord.option(name="state", description="Send announcements in this server")
    @analytics("user_settings birthday_announcements")
    async def set_birthday_announcement(self, ctx: discord.ApplicationContext, state: bool):
        set_per_user_setting(ctx.user.id, f'birthday_announcements_{str(ctx.guild.id)}', str(state).lower())
        if state:
            state_str = trl(ctx.user.id, ctx.guild.id, "per_user_birthday_announcements_enabled", append_tip=True)
        else:
            state_str = trl(ctx.user.id, ctx.guild.id, "per_user_birthday_announcements_disabled", append_tip=True)
        await ctx.respond(state_str, ephemeral=True)

    @user_settings_group.command(name='clear_birthday', description='Clear all data about your birthday from the bot')
    @analytics("user_settings clear_birthday")
    async def clear_birthday(self, ctx: discord.ApplicationContext):
        unset_per_user_setting(ctx.user.id, 'birthday_date')
        unset_per_user_setting(ctx.user.id, 'birthday_year')
        unset_per_user_setting(ctx.user.id, 'birthday_send_dm')
        await ctx.respond(trl(ctx.user.id, ctx.guild.id, "per_user_birthday_cleared", append_tip=True), ephemeral=True)

    @user_settings_group.command(name='tips', description='Enable or disable tips')
    @analytics('user_settings tips')
    async def set_tips(self, ctx: discord.ApplicationContext, state: bool):
        set_per_user_setting(ctx.user.id, 'tips_enabled', str(state).lower())
        if state:
            state_str = trl(ctx.user.id, ctx.guild.id, "per_user_tips_enabled", append_tip=True)
        else:
            state_str = trl(ctx.user.id, ctx.guild.id, "per_user_tips_disabled", append_tip=True)
        await ctx.respond(state_str, ephemeral=True)
