import re
from datetime import datetime

import discord

from utils.analytics import analytics
from utils.birthday_announcements import set_birthday, remove_birthday
from utils.languages import get_language_names, language_name_to_code, get_language_name, get_language
from utils.languages import get_translation_for_key_localized as trl
from utils.per_user_settings import set_per_user_setting, db_init, get_per_user_setting, unset_per_user_setting
from utils.tips import append_tip_to_message
from utils.tzutil import get_now_for_server


class PerUserSettings(discord.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

        self.bot.loop.create_task(db_init())

    user_settings_group = discord.SlashCommandGroup(name='user_settings', description='Per user settings')

    @user_settings_group.command(name='chat_streaks_alerts', description='Enable or disable chat streaks alerts')
    @discord.option(name='state', description='How notifications should be sent', choices=['enabled', 'only when lost', 'off'])
    @analytics("user_settings chat_streaks_alerts")
    async def chat_streaks_alerts(self, ctx: discord.ApplicationContext, state: str):
        await set_per_user_setting(ctx.user.id, 'chat_streaks_alerts', state)
        if state == 'enabled':
            state = await trl(ctx.user.id, ctx.guild.id, "per_user_chat_streak_state_enabled")
        elif state == 'only when lost':
            state = await trl(ctx.user.id, ctx.guild.id, "per_user_chat_streak_state_only_when_lost")
        else:
            state = await trl(ctx.user.id, ctx.guild.id, "per_user_chat_streak_state_disabled")
        await ctx.respond((await trl(ctx.user.id, ctx.guild.id, "per_user_chat_streak_response", append_tip=True)).format(state=state), ephemeral=True)

    @user_settings_group.command(name='langauge', description='Set your personal language, applies across servers for you')
    @discord.option(name='lang', description='Your language', choices=get_language_names())
    @analytics("user_settings language")
    async def set_language(self, ctx: discord.ApplicationContext, lang: str):
        lang_code = language_name_to_code(lang)

        await set_per_user_setting(ctx.user.id, 'language', lang_code)
        await ctx.respond((await trl(ctx.user.id, ctx.guild.id, "per_user_language_set", append_tip=True)).format(lang=get_language_name(lang_code, completeness=False)), ephemeral=True)

    @user_settings_group.command(name='birthday', description='Set your birthday for Birthday Announcements.')
    @discord.option(name='birthday', description='Your birthday in the format YYYY-MM-DD')
    @analytics("user_settings birthday")
    async def set_birthdate(self, ctx: discord.ApplicationContext, birthday: str):
        # Validate birthday using REGEX
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', birthday):
            await ctx.respond(await trl(ctx.user.id, ctx.guild.id, "per_user_birthday_invalid"), ephemeral=True)
            return

        # Validate valid year, month, and day
        if int(birthday[:4]) < 1900 or int(birthday[:4]) > (await get_now_for_server(ctx.guild.id)).year - 14 or int(birthday[5:7]) < 1 or int(birthday[5:7]) > 12 or int(birthday[8:]) < 1 or int(
                birthday[8:]) > 31:
            await ctx.respond(await trl(ctx.user.id, ctx.guild.id, "per_user_birthday_invalid"), ephemeral=True)
            return

        await set_birthday(ctx.user.id, datetime.strptime(birthday, '%Y-%m-%d'))
        await ctx.respond((await trl(ctx.user.id, ctx.guild.id, "per_user_birthday_set", append_tip=True)).format(birthday=birthday), ephemeral=True)

    @user_settings_group.command(name="birthday_settings", description="Personalize your birthday settings")
    @discord.option(name="send_dm", type=bool, description="Whether to allow this bot to send DMs to you")
    @analytics("user_settings birthday_settings")
    async def set_birthday_settings(self, ctx: discord.ApplicationContext, send_dm: bool | None = None):
        if send_dm is not None:
            await set_per_user_setting(ctx.user.id, 'birthday_send_dm', str(send_dm).lower())

        send_dm = await get_per_user_setting(ctx.user.id, 'birthday_send_dm', "false")
        send_dm = await trl(ctx.user.id, ctx.guild.id, "per_user_birthday_send_dm_enabled") if send_dm else await trl(ctx.user.id, ctx.guild.id, "per_user_birthday_send_dm_disabled",
                                                                                                                           append_tip=True)

        try:
            await ctx.user.send("This is a test message to see if I can send you DMs. If you can see this, then I can send you birthday announcements!")
        except discord.Forbidden:
            send_dm += "\n\n" + await trl(ctx.user.id, ctx.guild.id, "birthdays_enable_dms")

        send_dm = append_tip_to_message(ctx.guild.id, ctx.user.id, send_dm, await get_language(ctx.guild.id, ctx.user.id))
        await ctx.respond(f"{send_dm}", ephemeral=True)

    @user_settings_group.command(name="birthday_announcements", description="Whether to announce birthdays in the server you're currently in")
    @discord.option(name="state", description="Send announcements in this server")
    @analytics("user_settings birthday_announcements")
    async def set_birthday_announcement(self, ctx: discord.ApplicationContext, state: bool):
        await set_per_user_setting(ctx.user.id, f'birthday_announcements_{str(ctx.guild.id)}', str(state).lower())
        if state:
            state_str = await trl(ctx.user.id, ctx.guild.id, "per_user_birthday_announcements_enabled", append_tip=True)
        else:
            state_str = await trl(ctx.user.id, ctx.guild.id, "per_user_birthday_announcements_disabled", append_tip=True)
        await ctx.respond(state_str, ephemeral=True)

    @user_settings_group.command(name='clear_birthday', description='Clear all data about your birthday from the bot')
    @analytics("user_settings clear_birthday")
    async def clear_birthday(self, ctx: discord.ApplicationContext):
        await remove_birthday(ctx.user.id)
        await unset_per_user_setting(ctx.user.id, 'birthday_reveal_age')
        await unset_per_user_setting(ctx.user.id, 'birthday_send_dm')
        await ctx.respond(await trl(ctx.user.id, ctx.guild.id, "per_user_birthday_cleared", append_tip=True), ephemeral=True)

    @user_settings_group.command(name='tips', description='Enable or disable tips')
    @analytics('user_settings tips')
    async def set_tips(self, ctx: discord.ApplicationContext, state: bool):
        await set_per_user_setting(ctx.user.id, 'tips_enabled', str(state).lower())
        if state:
            state_str = await trl(ctx.user.id, ctx.guild.id, "per_user_tips_enabled", append_tip=True)
        else:
            state_str = await trl(ctx.user.id, ctx.guild.id, "per_user_tips_disabled", append_tip=True)
        await ctx.respond(state_str, ephemeral=True)
