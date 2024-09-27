import datetime

import discord
from discord.ext import tasks, commands

from utils.analytics import analytics
from utils.languages import get_translation_for_key_localized as trl
from utils.per_user_settings import search_settings_by_value, get_per_user_setting
from utils.settings import get_setting
from utils.settings import set_setting
from utils.tzutil import get_now_for_server


class BirthdayAnnouncements(discord.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        super().__init__()

    birthday_announcements_group = discord.SlashCommandGroup(name="birthday_announcements", description="Birthday Announcements commands")

    @birthday_announcements_group.command(name="channel", description="Set the channel for birthday announcements")
    @discord.default_permissions(manage_guild=True)
    @discord.option(name="channel", description="The channel to send birthday announcements in")
    @commands.has_permissions(manage_guild=True)
    @analytics("birthday_announcements channel")
    async def set_channel(self, ctx: discord.ApplicationContext, channel: discord.TextChannel):
        await set_setting(ctx.guild.id, "birthday_announcements_channel", str(channel.id))
        await ctx.respond(await trl(ctx.user.id, ctx.guild.id, "birthday_announcements_channel_set", append_tip=True).format(channel=channel.mention), ephemeral=True)

    @discord.Cog.listener()
    async def on_ready(self):
        self.birthday_announcements.start()

    @tasks.loop(seconds=60)
    async def birthday_announcements(self):
        await self.handle_birthday_announcements()

    async def handle_birthday_announcements(self):

        date_string = datetime.datetime.now().strftime("%m-%d")

        for guild in self.bot.guilds:
            birthday_announcements_channel = int(await get_setting(guild.id, "birthday_announcements_channel", "0"))
            if birthday_announcements_channel == 0:
                continue

            now = await get_now_for_server(guild.id)
            if now.hour != 12 or now.minute != 0:
                continue

            birthdays_this_day = await search_settings_by_value(date_string)
            for i in birthdays_this_day:
                member = guild.get_member(i[0])
                if member is None:
                    continue

                if get_per_user_setting(member.id, f'birthday_announcements_{str(guild.id)}', 'true') == 'true':
                    message = await get_setting(guild.id, "birthday_announcements_message", "Today is {mention}'s birthday! 🎉 Say happy birthday! 🎂")
                    message = message.replace("{mention}", member.mention)
                    message = message.replace("{name}", member.display_name)
                    message = message.replace("{guild}", guild.name)
                    message = message.replace("{birthday}", i[1])

                    if get_per_user_setting(member.id, 'birthday_reveal_age', 'false') == 'true':
                        message = message.replace("{age}", str(now.year - int(i[1][:4])))
                    else:
                        message = message.replace("{age}", "*this user's age is hidden*")

                    # Send the message
                    channel = guild.get_channel(birthday_announcements_channel)
                    await channel.send(message)

                # Send DM if enabled
                if get_per_user_setting(member.id, 'birthday_send_dm', 'false') == 'true':
                    try:
                        if get_per_user_setting(member.id, 'birthday_reveal_age', 'false'):
                            await member.send(await trl(member.id, 0, "birthday_dm_age").format(age=str(now.year - int(i[1][:4]))))
                        else:
                            await member.send(await trl(member.id, 0, "birthday_dm"))

                    except discord.Forbidden:
                        pass

    @birthday_announcements_group.command(name="message", description="Customize the birthday announcement message")
    @discord.option(name="message", description="The message to send on birthdays")
    @discord.default_permissions(manage_guild=True)
    @commands.has_permissions(manage_guild=True)
    @analytics("birthday_announcements message")
    async def birthday_announcements_message(self, ctx: discord.ApplicationContext, message: str):
        await set_setting(ctx.guild.id, "birthday_announcements_message", message)
        await ctx.respond("Birthday announcement message set", ephemeral=True)
