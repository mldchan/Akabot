import datetime
import re

import discord
import emoji
import sentry_sdk
from discord.ext import commands as commands_ext

from database import get_conn
from utils.analytics import analytics
from utils.languages import get_translation_for_key_localized as trl, get_language
from utils.logging_util import log_into_logs
from utils.per_user_settings import get_per_user_setting, set_per_user_setting
from utils.settings import get_setting, set_setting
from utils.tips import append_tip_to_message
from utils.tzutil import get_now_for_server


async def db_init():
    db = await get_conn()
    await db.execute("create table if not exists leveling (guild_id int, user_id int, xp int)")
    await db.execute("create table if not exists leveling_multiplier (guild_id int, name text, multiplier int, start_date text, end_date text)")
    await db.commit()
    await db.close()


async def db_calculate_multiplier(guild_id: int):
    multiplier = int(await get_setting(guild_id, 'leveling_xp_multiplier', '1'))

    multipliers = await db_multiplier_getall(guild_id)
    for m in multipliers:
        start_month, start_day = map(int, m[3].split('-'))
        end_month, end_day = map(int, m[4].split('-'))

        now = await get_now_for_server(guild_id)
        start_date = datetime.datetime(now.year, start_month, start_day)
        end_date = datetime.datetime(now.year, end_month, end_day, hour=23, minute=59, second=59)

        if end_date < start_date:
            end_date = end_date.replace(year=end_date.year + 1)

        if start_date <= now <= end_date:
            multiplier *= m[2]

    return multiplier


async def db_get_user_xp(guild_id: int, user_id: int):
    await db_init()
    db = await get_conn()
    cur = await db.execute('SELECT xp FROM leveling WHERE guild_id = ? AND user_id = ?', (guild_id, user_id))
    data = await cur.fetchone()
    await db.close()
    return data[0] if data else 1


async def db_add_user_xp(guild_id: int, user_id: int, xp: int):
    await db_init()

    db = await get_conn()
    cur = await db.execute("SELECT xp FROM leveling WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
    data = await cur.fetchone()
    if data:
        current_xp = data[0]
        multiplier = await db_calculate_multiplier(guild_id)
        await db.execute("UPDATE leveling SET xp = ? WHERE guild_id = ? AND user_id = ?", (current_xp + (xp * int(multiplier)), guild_id, user_id))
    else:
        await db.execute("INSERT INTO leveling (guild_id, user_id, xp) VALUES (?, ?, ?)", (guild_id, user_id, xp))
    await db.commit()
    await db.close()


async def get_level_for_xp(guild_id: int, xp: int):
    level = 0
    leveling_xp_per_level = await get_setting(guild_id, 'leveling_xp_per_level', '500')
    xp_needed = await db_calculate_multiplier(guild_id) * int(leveling_xp_per_level)
    while xp >= xp_needed:
        level += 1
        xp -= xp_needed
        xp_needed = await db_calculate_multiplier(guild_id) * int(leveling_xp_per_level)

    return level


async def get_xp_for_level(guild_id: int, level: int):
    xp = 0
    leveling_xp_per_level = await get_setting(guild_id, 'leveling_xp_per_level', '500')
    xp_needed = await db_calculate_multiplier(guild_id) * int(leveling_xp_per_level)
    for _ in range(level):
        xp += xp_needed
        xp_needed = await db_calculate_multiplier(guild_id) * int(leveling_xp_per_level)

    return xp


async def db_multiplier_add(guild_id: int, name: str, multiplier: int, start_date_month: int, start_date_day: int, end_date_month: int, end_date_day: int):
    await db_init()
    db = await get_conn()
    await db.execute("INSERT INTO leveling_multiplier (guild_id, name, multiplier, start_date, end_date) VALUES (?, ?, ?, ?, ?)",
                     (guild_id, name, multiplier, '{:02d}-{:02d}'.format(start_date_month, start_date_day), '{:02d}-{:02d}'.format(end_date_month, end_date_day)))
    await db.commit()
    await db.close()


async def db_multiplier_exists(guild_id: int, name: str):
    await db_init()
    db = await get_conn()
    cur = await db.execute("SELECT * FROM leveling_multiplier WHERE guild_id = ? AND name = ?", (guild_id, name))
    data = await cur.fetchone()
    await db.close()
    return data is not None


async def db_multiplier_change_name(guild_id: int, old_name: str, new_name: str):
    await db_init()
    db = await get_conn()
    await db.execute("UPDATE leveling_multiplier SET name = ? WHERE guild_id = ? AND name = ?", (new_name, guild_id, old_name))
    await db.commit()
    await db.close()


async def db_multiplier_change_multiplier(guild_id: int, name: str, multiplier: int):
    await db_init()
    db = await get_conn()
    await db.execute("UPDATE leveling_multiplier SET multiplier = ? WHERE guild_id = ? AND name = ?", (multiplier, guild_id, name))
    await db.commit()
    await db.close()


async def db_multiplier_change_start_date(guild_id: int, name: str, start_date: datetime.datetime):
    await db_init()
    db = await get_conn()
    await db.execute("UPDATE leveling_multiplier SET start_date = ? WHERE guild_id = ? AND name = ?", (start_date, guild_id, name))
    await db.commit()
    await db.close()


async def db_multiplier_change_end_date(guild_id: int, name: str, end_date: datetime.datetime):
    await db_init()
    db = await get_conn()
    await db.execute("UPDATE leveling_multiplier SET end_date = ? WHERE guild_id = ? AND name = ?", (end_date, guild_id, name))
    await db.commit()
    await db.close()


async def db_multiplier_remove(guild_id: int, name: str):
    await db_init()
    db = await get_conn()
    await db.execute("DELETE FROM leveling_multiplier WHERE guild_id = ? AND name = ?", (guild_id, name))
    await db.commit()
    await db.close()


async def db_multiplier_getall(guild_id: int):
    await db_init()
    db = await get_conn()
    cur = await db.execute("SELECT * FROM leveling_multiplier WHERE guild_id = ?", (guild_id,))
    data = await cur.fetchall()
    await db.close()
    return data


async def db_multiplier_get(guild_id: int, name: str):
    await db_init()
    db = await get_conn()
    cur = await db.execute("SELECT * FROM leveling_multiplier WHERE guild_id = ? AND name = ?", (guild_id, name))
    data = await cur.fetchone()
    await db.close()
    return data


def validate_day(month: int, day: int, year: int) -> bool:
    """
    Validates if the given day is correct for the specified month and year.

    Args:
    - month (int): The month (1-12).
    - day (int): The day of the month to validate.
    - year (int): The year, used to check for leap years.

    Returns:
    - bool: True if the day is valid for the given month and year, False otherwise.
    """

    # Check for valid month
    if not 1 <= month <= 12:
        return False

    # Check for valid day
    if not 1 <= day <= 31:
        return False

    # Function to check if a year is a leap year
    def is_leap_year(year: int) -> bool:
        return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)

    # February: check for leap year
    if month == 2:
        if is_leap_year(year):
            return day <= 29
        else:
            return day <= 28

    # April, June, September, November: 30 days
    if month in [4, 6, 9, 11]:
        return day <= 30

    # For all other months, the day is valid if it's 31 or less
    return True


async def update_roles_for_member(guild: discord.Guild, member: discord.Member):
    xp = await db_get_user_xp(guild.id, member.id)
    level = await get_level_for_xp(guild.id, xp)

    for i in range(1, level + 1):  # Add missing roles
        role_id = await get_setting(guild.id, f'leveling_reward_{i}', '0')
        if role_id != '0':
            role = guild.get_role(int(role_id))
            if role.position > guild.me.top_role.position:
                return

            if role is not None and role not in member.roles:
                await member.add_roles(role)

    for i in range(level + 1, 100):  # Remove excess roles
        role_id = await get_setting(guild.id, f'leveling_reward_{i}', '0')
        if role_id != '0':
            role = guild.get_role(int(role_id))
            if role.position > guild.me.top_role.position:
                return

            if role is not None and role in member.roles:
                await member.remove_roles(role)


class Leveling(discord.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot
        super().__init__()

    @discord.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot:
            return

        before_level = get_level_for_xp(msg.guild.id, await db_get_user_xp(msg.guild.id, msg.author.id))
        await db_add_user_xp(msg.guild.id, msg.author.id, 3)
        after_level = get_level_for_xp(msg.guild.id, await db_get_user_xp(msg.guild.id, msg.author.id))

        if not msg.channel.permissions_for(msg.guild.me).send_messages:
            return

        if msg.guild.me.guild_permissions.manage_roles:
            await update_roles_for_member(msg.guild, msg.author)

        if before_level != after_level and msg.channel.can_send():
            try:
                msg2 = await msg.channel.send((await trl(msg.author.id, msg.guild.id, "leveling_level_up")).format(mention=msg.author.mention, level=str(after_level)))
                await msg2.delete(delay=5)
            except Exception as e:
                sentry_sdk.capture_exception(e)

    @discord.slash_command(name='level', description='Get the level of a user')
    @commands_ext.guild_only()
    @analytics("level")
    async def get_level(self, ctx: discord.ApplicationContext, user: discord.User = None):
        user = user or ctx.user

        level_xp = db_get_user_xp(ctx.guild.id, user.id)
        level = get_level_for_xp(ctx.guild.id, level_xp)
        multiplier = db_calculate_multiplier(ctx.guild.id)
        next_level_xp = get_xp_for_level(ctx.guild.id, level + 1)
        multiplier_list = db_multiplier_getall(ctx.guild.id)

        msg = ""
        for i in multiplier_list:
            start_month, start_day = map(int, i[3].split('-'))
            end_month, end_day = map(int, i[4].split('-'))

            now = await get_now_for_server(ctx.guild.id)
            start_date = datetime.datetime(now.year, start_month, start_day)
            end_date = datetime.datetime(now.year, end_month, end_day, hour=23, minute=59, second=59)

            if end_date < start_date:
                end_date = end_date.replace(year=end_date.year + 1)

            # continue if the multiplier is not active
            if start_date > now or end_date < now:
                continue

            msg += (await trl(ctx.user.id, ctx.guild.id, "leveling_level_multiplier_row")).format(name=i[1], multiplier=i[2], start=i[3], end=i[4])

        if user == ctx.user:
            icon = get_per_user_setting(ctx.user.id, 'leveling_icon', '')
            response = (await trl(ctx.user.id, ctx.guild.id, "leveling_level_info_self")).format(icon=icon, level=level, level_xp=level_xp, next_level_xp=next_level_xp, next_level=level + 1,
                                                                                               multiplier=multiplier)

            if len(msg) > 0:
                response += await trl(ctx.user.id, ctx.guild.id, "leveling_level_multiplier_title")
                response += f'{msg}'

            await ctx.respond(response, ephemeral=True)
        else:
            icon = get_per_user_setting(user.id, 'leveling_icon', '')
            response = (await trl(ctx.user.id, ctx.guild.id, "leveling_level_info_another")).format(icon=icon, user=user.mention, level=level, level_xp=level_xp, next_level_xp=next_level_xp,
                                                                                                  next_level=level + 1,
                                                                                                  multiplier=multiplier)

            if len(msg) > 0:
                response += await trl(ctx.user.id, ctx.guild.id, "leveling_level_multiplier_title")
                response += f'{msg}'

            if get_per_user_setting(ctx.user.id, 'tips_enabled', 'true') == 'true':
                language = await get_language(ctx.guild.id, ctx.user.id)
                response = append_tip_to_message(ctx.guild.id, ctx.user.id, response, language)
            await ctx.respond(response, ephemeral=True)

    leveling_subcommand = discord.SlashCommandGroup(name='leveling', description='Leveling settings')

    @leveling_subcommand.command(name="list", description="List the leveling settings")
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @analytics("leveling list")
    async def list_settings(self, ctx: discord.ApplicationContext):
        leveling_xp_multiplier = await get_setting(ctx.guild.id, 'leveling_xp_multiplier', '1')

        multiplier_list = db_multiplier_getall(ctx.guild.id)
        multiplier_list_msg = ""

        for i in multiplier_list:
            multiplier_list_msg += (await trl(ctx.user.id, ctx.guild.id, "leveling_level_multiplier_row")).format(name=i[1], multiplier=i[2], start=i[3], end=i[4])

        if len(multiplier_list) != 0:
            multiplier_list_msg = await trl(ctx.user.id, ctx.guild.id, "leveling_level_multiplier_title") + multiplier_list_msg
        else:
            multiplier_list_msg = await trl(ctx.user.id, ctx.guild.id, "leveling_level_multipliers_none")

        embed = discord.Embed(title=await trl(ctx.user.id, ctx.guild.id, "leveling_settings_title"), color=discord.Color.blurple(), description=multiplier_list_msg)
        embed.add_field(name=await trl(ctx.user.id, ctx.guild.id, "leveling_settings_multiplier"), value=f'`{leveling_xp_multiplier}x`')

        await ctx.respond(embed=embed, ephemeral=True)

    @leveling_subcommand.command(name='multiplier', description='Set the leveling multiplier')
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @discord.option(name="multiplier", description="The multiplier to set", type=int)
    @analytics("leveling multiplier")
    async def set_multiplier(self, ctx: discord.ApplicationContext, multiplier: int):
        # Get old setting
        old_multiplier = await get_setting(ctx.guild.id, 'leveling_xp_multiplier', str(multiplier))

        # Set new setting
        await set_setting(ctx.guild.id, 'leveling_xp_multiplier', str(multiplier))

        # Create message
        logging_embed = discord.Embed(title=await trl(ctx.user.id, ctx.guild.id, "leveling_set_multiplier_log_title"))
        logging_embed.add_field(name=await trl(ctx.user.id, ctx.guild.id, "logging_user"), value=f"{ctx.user.mention}")
        logging_embed.add_field(name=await trl(ctx.user.id, ctx.guild.id, "leveling_log_multiplier"), value=f"{old_multiplier} -> {str(multiplier)}")

        # Send to logs
        await log_into_logs(ctx.guild, logging_embed)

        # Send response
        await ctx.respond((await trl(ctx.user.id, ctx.guild.id, "leveling_set_multiplier_success", append_tip=True)).format(multiplier=multiplier), ephemeral=True)

    @leveling_subcommand.command(name='add_multiplier', description='Add to the leveling multiplier')
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @discord.option(name="name", description="The name of the multiplier", type=str)
    @discord.option(name="multiplier", description="The multiplication", type=int)
    @discord.option(name='start_date', description='The start date of the multiplier, in format MM-DD', type=str)
    @discord.option(name='end_date', description='The end date of the multiplier, in format MM-DD', type=str)
    @analytics("leveling add multiplier")
    async def add_multiplier(self, ctx: discord.ApplicationContext, name: str, multiplier: int, start_date: str, end_date: str):
        # Verify the format of start_date and end_date
        if not re.match(r'\d{2}-\d{2}', start_date) or not re.match(r'\d{2}-\d{2}', end_date):
            await ctx.respond(await trl(ctx.user.id, ctx.guild.id, "leveling_error_invalid_date_format"), ephemeral=True)
            return

        # Verify if the multiplier already exists
        if db_multiplier_exists(ctx.guild.id, name):
            await ctx.respond((await trl(ctx.user.id, ctx.guild.id, "leveling_multiplier_already_exists")).format(name=name), ephemeral=True)
            return

        # Verify the month and day values
        start_month, start_day = map(int, start_date.split('-'))
        end_month, end_day = map(int, end_date.split('-'))

        now = await get_now_for_server(ctx.guild.id)
        # Use the validate_day method to check if the start and end dates are valid
        if not validate_day(start_month, start_day, now.year):
            await ctx.respond(await trl(ctx.user.id, ctx.guild.id, "leveling_error_invalid_start_date"), ephemeral=True)
            return

        if not validate_day(end_month, end_day, now.year):
            await ctx.respond(await trl(ctx.user.id, ctx.guild.id, "leveling_error_invalid_end_date"), ephemeral=True)
            return

        # Multipliers apply to every year
        db_multiplier_add(ctx.guild.id, name, multiplier, start_month, start_day, end_month, end_day)

        # Logging embed
        logging_embed = discord.Embed(title=await trl(0, ctx.guild.id, "leveling_add_multiplier_log_title"))
        logging_embed.add_field(name=await trl(0, ctx.guild.id, "logging_user"), value=f"{ctx.user.mention}")
        logging_embed.add_field(name=await trl(0, ctx.guild.id, "logging_name"), value=f"{name}")
        logging_embed.add_field(name=await trl(0, ctx.guild.id, "leveling_log_multiplier"), value=f"{multiplier}")
        logging_embed.add_field(name=await trl(0, ctx.guild.id, "leveling_log_start_date"), value=f"{start_date}")
        logging_embed.add_field(name=await trl(0, ctx.guild.id, "leveling_log_end_date"), value=f"{end_date}")

        # Send into logs
        await log_into_logs(ctx.guild, logging_embed)

        # Send response
        await ctx.respond((await trl(ctx.user.id, ctx.guild.id, "leveling_add_multiplier_success", append_tip=True)).format(name=name, multiplier=multiplier), ephemeral=True)

    @leveling_subcommand.command(name='change_multiplier_name', description='Change the name of a multiplier')
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @discord.option(name="old_name", description="The old name of the multiplier", type=str)
    @discord.option(name="new_name", description="The new name of the multiplier", type=str)
    @analytics("leveling change multiplier name")
    async def change_multiplier_name(self, ctx: discord.ApplicationContext, old_name: str, new_name: str):
        if not db_multiplier_exists(ctx.guild.id, old_name):
            await ctx.respond((await trl(ctx.user.id, ctx.guild.id, "leveling_multiplier_doesnt_exist")).format(name=old_name), ephemeral=True)
            return

        if db_multiplier_exists(ctx.guild.id, new_name):
            await ctx.respond((await trl(ctx.user.id, ctx.guild.id, "leveling_multiplier_already_exists")).format(name=new_name), ephemeral=True)
            return

        # Set new setting
        await db_multiplier_change_name(ctx.guild.id, old_name, new_name)

        # Logging embed
        logging_embed = discord.Embed(title=await trl(0, ctx.guild.id, "leveling_rename_multiplier_log_title"))
        logging_embed.add_field(name=await trl(0, ctx.guild.id, "logging_user"), value=f"{ctx.user.mention}")
        logging_embed.add_field(name=await trl(0, ctx.guild.id, "leveling_rename_multiplier_log_old_name"), value=f"{old_name}")
        logging_embed.add_field(name=await trl(0, ctx.guild.id, "leveling_rename_multiplier_log_new_name"), value=f"{new_name}")

        # Send into logs
        await log_into_logs(ctx.guild, logging_embed)

        # Send response
        await ctx.respond((await trl(ctx.user.id, ctx.guild.id, "leveling_rename_multiplier_success", append_tip=True)).format(old_name=old_name, new_name=new_name), ephemeral=True)

    @leveling_subcommand.command(name='change_multiplier_multiplier', description='Change the multiplier of a multiplier')
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @discord.option(name="name", description="The name of the multiplier", type=str)
    @discord.option(name="multiplier", description="The new multiplier", type=int)
    @analytics("leveling change multiplier multiplier")
    async def change_multiplier_multiplier(self, ctx: discord.ApplicationContext, name: str, multiplier: int):
        if not db_multiplier_exists(ctx.guild.id, name):
            await ctx.respond(await trl(ctx.user.id, ctx.guild.id, "leveling_multiplier_doesnt_exist"), ephemeral=True)
            return

        # Get old setting
        old_multiplier = db_multiplier_get(ctx.guild.id, name)[2]

        # Set new setting
        db_multiplier_change_multiplier(ctx.guild.id, name, multiplier)

        # Logging embed
        logging_embed = discord.Embed(title=await trl(0, ctx.guild.id, "leveling_multiplier_logs_title"))
        logging_embed.add_field(name=await trl(0, ctx.guild.id, "logging_user"), value=f"{ctx.user.mention}")
        logging_embed.add_field(name=await trl(0, ctx.guild.id, "logging_name"), value=f"{name}")
        logging_embed.add_field(name=await trl(0, ctx.guild.id, "leveling_multiplier_logs_old_multiplier"), value=f"{old_multiplier}")
        logging_embed.add_field(name=await trl(0, ctx.guild.id, "leveling_multiplier_logs_new_multiplier"), value=f"{multiplier}")

        # Send into logs
        await log_into_logs(ctx.guild, logging_embed)

        # Send response
        await ctx.respond((await trl(ctx.user.id, ctx.guild.id, "leveling_multiplier_success", append_tip=True)).format(name=name, multiplier=multiplier), ephemeral=True)

    @leveling_subcommand.command(name='change_multiplier_start_date', description='Change the start date of a multiplier')
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @discord.option(name="name", description="The name of the multiplier", type=str)
    @discord.option(name="start_date", description="The new start date of the multiplier, in format MM-DD", type=str)
    @analytics("leveling change multiplier start date")
    async def change_multiplier_start_date(self, ctx: discord.ApplicationContext, name: str, start_date: str):
        if not await db_multiplier_exists(ctx.guild.id, name):
            await ctx.respond((await trl(ctx.user.id, ctx.guild.id, "leveling_multiplier_doesnt_exist")).format(name=name), ephemeral=True)
            return

        # Verify the format of start_date
        if not re.match(r'\d{2}-\d{2}', start_date):
            await ctx.respond(await trl(ctx.user.id, ctx.guild.id, "leveling_error_invalid_date_format"), ephemeral=True)
            return

        # Verify the month and day values
        start_month, start_day = map(int, start_date.split('-'))

        now = await get_now_for_server(ctx.guild.id)
        # Use the validate_day method to check if the start date is valid
        if not validate_day(start_month, start_day, now.year):
            await ctx.respond(await trl(ctx.user.id, ctx.guild.id, "leveling_error_invalid_start_date"), ephemeral=True)
            return

        start_year = now.year

        # Set new setting
        await db_multiplier_change_start_date(ctx.guild.id, name, datetime.datetime(start_year, start_month, start_day))

        # Logging embed
        logging_embed = discord.Embed(title=await trl(0, ctx.guild.id, "leveling_start_date_log_title"))
        logging_embed.add_field(name=await trl(0, ctx.guild.id, "logging_user"), value=f"{ctx.user.mention}")
        logging_embed.add_field(name=await trl(0, ctx.guild.id, "logging_name"), value=f"{name}")
        logging_embed.add_field(name=await trl(0, ctx.guild.id, "leveling_start_date_new_start_date"), value=f"{start_date}")

        # Send into logs
        await log_into_logs(ctx.guild, logging_embed)

        # Send response
        await ctx.respond((await trl(ctx.user.id, ctx.guild.id, "leveling_start_date_success", append_tip=True)).format(name=name, start_date=start_date), ephemeral=True)

    @leveling_subcommand.command(name='change_multiplier_end_date', description='Change the end date of a multiplier')
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @discord.option(name="name", description="The name of the multiplier", type=str)
    @discord.option(name="end_date", description="The new end date of the multiplier, in format MM-DD", type=str)
    @analytics("leveling change multiplier end date")
    async def change_multiplier_end_date(self, ctx: discord.ApplicationContext, name: str, end_date: str):
        if not db_multiplier_exists(ctx.guild.id, name):
            await ctx.respond((await trl(ctx.user.id, ctx.guild.id, "leveling_multiplier_doesnt_exist")).format(name=name), ephemeral=True)
            return

        # Verify the format of end_date
        if not re.match(r'\d{2}-\d{2}', end_date):
            await ctx.respond(await trl(ctx.user.id, ctx.guild.id, "leveling_error_invalid_date_format"), ephemeral=True)
            return

        # Verify the month and day values
        end_month, end_day = map(int, end_date.split('-'))

        now = get_now_for_server(ctx.guild.id)
        # Use the validate_day method to check if the end date is valid
        if not validate_day(end_month, end_day, now.year):
            await ctx.respond(await trl(ctx.user.id, ctx.guild.id, "leveling_error_invalid_end_date"), ephemeral=True)
            return

        year = now.year

        # Set new setting
        db_multiplier_change_end_date(ctx.guild.id, name, datetime.datetime(year, end_month, end_day))

        # Logging embed
        logging_embed = discord.Embed(title=await trl(0, ctx.guild.id, "leveling_end_date_log_title"))
        logging_embed.add_field(name=await trl(0, ctx.guild.id, "logging_user"), value=f"{ctx.user.mention}")
        logging_embed.add_field(name=await trl(0, ctx.guild.id, "logging_name"), value=f"{name}")
        logging_embed.add_field(name=await trl(0, ctx.guild.id, "leveling_error_invalid_end_date"), value=f"{end_date}")

        # Send into logs
        await log_into_logs(ctx.guild, logging_embed)

        # Send response
        await ctx.respond((await trl(ctx.user.id, ctx.guild.id, "leveling_end_date_success", append_tip=True)).format(name=name, end_date=end_date), ephemeral=True)

    @leveling_subcommand.command(name='remove_multiplier', description='Remove a multiplier')
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @discord.option(name="name", description="The name of the multiplier", type=str)
    @analytics("leveling remove multiplier")
    async def remove_multiplier(self, ctx: discord.ApplicationContext, name: str):
        if not db_multiplier_exists(ctx.guild.id, name):
            await ctx.respond((await trl(ctx.user.id, ctx.guild.id, "leveling_multiplier_doesnt_exist")).format(name=name), ephemeral=True)
            return

        # Get old setting
        old_multiplier = db_multiplier_get(ctx.guild.id, name)[2]

        # Set new setting
        db_multiplier_remove(ctx.guild.id, name)

        # Logging embed
        logging_embed = discord.Embed(title=await trl(ctx.user.id, ctx.guild.id, "leveling_remove_multiplier_log_title"))
        logging_embed.add_field(name=await trl(ctx.user.id, ctx.guild.id, "logging_user"), value=f"{ctx.user.mention}")
        logging_embed.add_field(name=await trl(ctx.user.id, ctx.guild.id, "logging_name"), value=f"{name}")
        logging_embed.add_field(name=await trl(ctx.user.id, ctx.guild.id, "leveling_log_multiplier"), value=f"{old_multiplier}")

        # Send into logs
        await log_into_logs(ctx.guild, logging_embed)

        # Send response
        await ctx.respond((await trl(ctx.user.id, ctx.guild.id, "leveling_remove_multiplier_success", append_tip=True)).format(name=name), ephemeral=True)

    @leveling_subcommand.command(name='get_multiplier', description='Get the leveling multiplier')
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @analytics("leveling get multiplier")
    async def get_multiplier(self, ctx: discord.ApplicationContext):
        multiplier = db_calculate_multiplier(ctx.guild.id)
        await ctx.respond((await trl(ctx.user.id, ctx.guild.id, "leveling_get_multiplier_response", append_tip=True)).format(multiplier=multiplier), ephemeral=True)

    @leveling_subcommand.command(name='set_xp_per_level', description='Set the XP per level')
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @discord.option(name="xp", description="The XP to set", type=int)
    @analytics("leveling set xp per level")
    async def set_xp_per_level(self, ctx: discord.ApplicationContext, xp: int):
        old_xp = await get_setting(ctx.guild.id, 'leveling_xp_per_level', '500')
        await set_setting(ctx.guild.id, 'leveling_xp_per_level', str(xp))
        await ctx.respond((await trl(ctx.user.id, ctx.guild.id, "leveling_set_xp_per_level_success", append_tip=True)).format(xp=xp), ephemeral=True)

        # Logging embed
        logging_embed = discord.Embed(title=await trl(0, ctx.guild.id, "leveling_set_xp_per_level_log_title"))
        logging_embed.add_field(name=await trl(0, ctx.guild.id, "logging_user"), value=f"{ctx.user.mention}")
        logging_embed.add_field(name=await trl(0, ctx.guild.id, "leveling_set_xp_per_level_log_old_xp"), value=f"{old_xp}")
        logging_embed.add_field(name=await trl(0, ctx.guild.id, "leveling_set_xp_per_level_log_new_xp"), value=f"{xp}")

        # Send into logs
        await log_into_logs(ctx.guild, logging_embed)

    @leveling_subcommand.command(name='set_reward', description='Set a role for a level')
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @discord.option(name="level", description="The level to set the reward for", type=int)
    @discord.option(name='role', description='The role to set', type=discord.Role)
    @analytics("leveling set reward")
    async def set_reward(self, ctx: discord.ApplicationContext, level: int, role: discord.Role):
        # Get old setting
        old_role_id = await get_setting(ctx.guild.id, f"leveling_reward_{level}", '0')
        old_role = ctx.guild.get_role(int(old_role_id))

        # Set new setting
        await set_setting(ctx.guild.id, f'leveling_reward_{level}', str(role.id))

        # Logging embed
        logging_embed = discord.Embed(title=await trl(0, ctx.guild.id, "leveling_set_reward_log_title"))
        logging_embed.add_field(name=await trl(0, ctx.guild.id, "logging_user"), value=f"{ctx.user.mention}")
        if old_role_id == '0':
            logging_embed.add_field(name=await trl(0, ctx.guild.id, "logging_role"), value=(await trl(0, ctx.guild.id, "leveling_set_reward_log_role_added")).format(reward=role.mention))
        else:
            logging_embed.add_field(name=await trl(0, ctx.guild.id, "logging_role"),
                                    value=(await trl(0, ctx.guild.id, "leveling_set_reward_log_role_changed")).format(old_reward=old_role.mention if old_role is not None else old_role_id,
                                                                                                                    new_reward=role.mention))

        # Send into logs
        await log_into_logs(ctx.guild, logging_embed)

        # Send response
        await ctx.respond((await trl(ctx.user.id, ctx.guild.id, "leveling_set_reward_success", append_tip=True)).format(level=level, reward=role.mention), ephemeral=True)

    @leveling_subcommand.command(name='remove_reward', description='Remove a role for a level')
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @discord.option(name="level", description="The level to remove the reward for", type=int)
    @analytics("leveling remove reward")
    async def remove_reward(self, ctx: discord.ApplicationContext, level: int):
        # Get old settingF
        old_role_id = await get_setting(ctx.guild.id, f"leveling_reward_{level}", '0')
        old_role = ctx.guild.get_role(int(old_role_id))

        # Logging embed
        logging_embed = discord.Embed(title=await trl(ctx.user.id, ctx.guild.id, "leveling_remove_reward_log_title"))
        logging_embed.add_field(name=await trl(ctx.user.id, ctx.guild.id, "logging_user"), value=f"{ctx.user.mention}")
        if old_role is not None:
            logging_embed.add_field(name=await trl(ctx.user.id, ctx.guild.id, "logging_role"), value=f"{old_role.mention}")
        else:
            logging_embed.add_field(name=await trl(ctx.user.id, ctx.guild.id, "logging_role"), value=await trl(ctx.user.id, ctx.guild.id, "leveling_remove_reward_log_role_unknown"))

        # Send into logs
        await log_into_logs(ctx.guild, logging_embed)

        # Set new setting
        await set_setting(ctx.guild.id, f'leveling_reward_{level}', '0')

        # Send response
        await ctx.respond((await trl(ctx.user.id, ctx.guild.id, "leveling_remove_reward_success", append_tip=True)).format(level=level), ephemeral=True)

    @leveling_subcommand.command(name="set_icon", description="Set leveling icon")
    @analytics("leveling set icon")
    @commands_ext.guild_only()
    async def set_icon(self, ctx: discord.ApplicationContext, icon: str):

        success = False
        if emoji.is_emoji(icon):
            set_per_user_setting(ctx.user.id, 'leveling_icon', icon)
            success = True

        if re.match("<a?:[a-zA-Z0-9_]+:[0-9]+>", icon):
            set_per_user_setting(ctx.user.id, 'leveling_icon', icon)
            success = True

        if success:
            await ctx.respond((await trl(ctx.user.id, ctx.guild.id, "leveling_set_icon_success", append_tip=True)).format(icon=icon), ephemeral=True)
        else:
            await ctx.respond(await trl(ctx.user.id, ctx.guild.id, "leveling_set_icon_error"), ephemeral=True)
