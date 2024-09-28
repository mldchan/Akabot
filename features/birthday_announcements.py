import discord
from discord.ext import tasks, commands

from database import get_conn
from utils.analytics import analytics
from utils.birthday_announcements import get_birthdays_today, get_age_of_user
from utils.languages import get_translation_for_key_localized as trl
from utils.per_user_settings import get_per_user_setting
from utils.settings import get_setting
from utils.settings import set_setting
from utils.tzutil import get_now_for_server


class BirthdayAnnouncements(discord.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        super().__init__()

    birthday_announcements_group = discord.SlashCommandGroup(name="birthday_announcements", description="Birthday Announcements commands")

    @discord.Cog.listener()
    async def on_ready(self):
        db = await get_conn()
        await db.execute('create table if not exists birthdays(user_id integer primary key, current_age int, birthday text)')
        await db.commit()
        await db.close()

    @birthday_announcements_group.command(name="channel", description="Set the channel for birthday announcements")
    @discord.default_permissions(manage_guild=True)
    @discord.option(name="channel", description="The channel to send birthday announcements in")
    @commands.has_permissions(manage_guild=True)
    @analytics("birthday_announcements channel")
    async def set_channel(self, ctx: discord.ApplicationContext, channel: discord.TextChannel):
        await set_setting(ctx.guild.id, "birthday_announcements_channel", str(channel.id))
        await ctx.respond((await trl(ctx.user.id, ctx.guild.id, "birthday_announcements_channel_set", append_tip=True)).format(channel=channel.mention), ephemeral=True)

    @discord.Cog.listener()
    async def on_ready(self):
        self.birthday_announcements.start()

    @tasks.loop(seconds=60)
    async def birthday_announcements(self):
        await self.handle_birthday_announcements()

    @tasks.loop(seconds=60)
    async def handle_birthday_announcements(self):
        for guild in self.bot.guilds:
            now = await get_now_for_server(guild.id)
            (hour, minute) = (now.hour, now.minute)
            if hour != 12 and minute != 0:
                continue

            for birthday in await get_birthdays_today():
                user = guild.get_member(birthday[0])
                if user is None:
                    continue

                send_dm = await get_per_user_setting(user.id, "birthday_send_dm", "true") == "true"

                if send_dm:
                    try:
                        await user.send(await trl(user.id, guild.id, "birthday_dm"))
                    except discord.Forbidden:
                        pass

                if await get_per_user_setting(user.id, f"birthday_announcements_{guild.id}", "true") == "true":
                    channel_id = await get_setting(guild.id, "birthday_announcements_channel", "0")
                    channel = guild.get_channel(int(channel_id))
                    if channel is None:
                        continue

                    message = await get_setting(guild.id, "birthday_announcements_message", "Happy birthday {user}!")
                    message = message.replace("{date}", now.strftime("%B %d"))
                    message = message.replace("{year}", str(now.year))
                    message = message.replace("{time}", now.strftime("%H:%M"))
                    message = message.replace("{age}", str(await get_age_of_user(user.id)))
                    message = message.replace("{user}", user.mention)
                    message = message.replace("{username}", user.display_name)
                    message = message.replace("{server}", guild.name)
                    message = message.replace("{server_id}", str(guild.id))
                    message = message.replace("{user_id}", str(user.id))

                    await channel.send(message)


    @birthday_announcements_group.command(name="message", description="Customize the birthday announcement message")
    @discord.option(name="message", description="The message to send on birthdays")
    @discord.default_permissions(manage_guild=True)
    @commands.has_permissions(manage_guild=True)
    @analytics("birthday_announcements message")
    async def birthday_announcements_message(self, ctx: discord.ApplicationContext, message: str):
        await set_setting(ctx.guild.id, "birthday_announcements_message", message)
        await ctx.respond("Birthday announcement message set", ephemeral=True)
