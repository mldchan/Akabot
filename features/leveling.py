import datetime

import discord
from discord.ext import commands as commands_ext
import sentry_sdk

from database import conn as db
from utils.analytics import analytics
from utils.blocked import is_blocked
from utils.settings import get_setting, set_setting
from utils.logging import log_into_logs

def db_init():
    cur = db.cursor()
    cur.execute("create table if not exists leveling (guild_id int, user_id int, xp int)")
    cur.close()
    db.commit()


def db_calculate_multiplier(guild_id: int):
    multiplier = get_setting(guild_id, 'leveling_xp_multiplier', '1')
    weekend_event = get_setting(guild_id, 'weekend_event_enabled', 'false')
    weekend_event_multiplier = get_setting(guild_id, 'weekend_event_multiplier', '2')
    if weekend_event == 'true':
        if datetime.datetime.now().weekday() in [5, 6]:
            multiplier = str(int(multiplier) * int(weekend_event_multiplier))

    return multiplier


def db_get_user_xp(guild_id: int, user_id: int):
    db_init()
    cur = db.cursor()
    cur.execute('SELECT xp FROM leveling WHERE guild_id = ? AND user_id = ?', (guild_id, user_id))
    data = cur.fetchone()
    cur.close()
    return data[0] if data else 1


def db_add_user_xp(guild_id: int, user_id: int, xp: int):
    db_init()
    cur = db.cursor()
    cur.execute("SELECT xp FROM leveling WHERE guild_id = ? AND user_id = ?", (guild_id, user_id))
    data = cur.fetchone()
    if data:
        current_xp = data[0]
        multiplier = db_calculate_multiplier(guild_id)
        cur.execute("UPDATE leveling SET xp = ? WHERE guild_id = ? AND user_id = ?",
                    (current_xp + (xp * int(multiplier)), guild_id, user_id))
    else:
        cur.execute("INSERT INTO leveling (guild_id, user_id, xp) VALUES (?, ?, ?)", (guild_id, user_id, xp))
    cur.close()
    db.commit()


def get_xp_for_level(level: int):
    current = 0
    xp = 500
    iter = 0
    while current < level:
        if iter >= 10000000:
            raise OverflowError('Iteration limit reached.')
        xp *= 2
        current += 1
        iter += 1

    return xp


def get_level_for_xp(xp: int):
    current = 0
    level = 0
    iter = 0
    while current < xp:
        if iter >= 10000000:
            raise OverflowError('Iteration limit reached.')
        current += 500 * (2 ** level)
        level += 1
        iter += 1

    return level


async def update_roles_for_member(guild: discord.Guild, member: discord.Member):
    xp = db_get_user_xp(guild.id, member.id)
    level = get_level_for_xp(xp)

    for i in range(1, level + 1):  # Add missing roles
        role_id = get_setting(guild.id, f'leveling_reward_{i}', '0')
        if role_id != '0':
            role = guild.get_role(int(role_id))
            if role.position > guild.me.top_role.position:
                return

            if role is not None and role not in member.roles:
                await member.add_roles(role)

    for i in range(level + 1, 100):  # Remove excess roles
        role_id = get_setting(guild.id, f'leveling_reward_{i}', '0')
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
        
        before_level = get_level_for_xp(db_get_user_xp(msg.guild.id, msg.author.id))
        db_add_user_xp(msg.guild.id, msg.author.id, 3)
        after_level = get_level_for_xp(db_get_user_xp(msg.guild.id, msg.author.id))

        if not msg.channel.permissions_for(msg.guild.me).send_messages:
            return

        if msg.guild.me.guild_permissions.manage_roles:
            await update_roles_for_member(msg.guild, msg.author)

        if before_level != after_level and msg.channel.can_send():
            try:
                msg2 = await msg.channel.send(
                f'Congratulations, {msg.author.mention}! You have reached level {after_level}!')
                await msg2.delete(delay=5)
            except Exception as e:
                sentry_sdk.capture_exception(e)

    @discord.slash_command(name='level', description='Get the level of a user')
    @commands_ext.guild_only()
    @is_blocked()
    @analytics("level")
    async def get_level(self, ctx: discord.ApplicationContext, user: discord.User = None):
        user = user or ctx.user

        level = get_level_for_xp(db_get_user_xp(ctx.guild.id, user.id))

        await ctx.respond(
            f'{user.mention} is level {level}.\nThe multiplier is currently `{str(db_calculate_multiplier(ctx.guild.id))}x`.',
            ephemeral=True)

    leveling_subcommand = discord.SlashCommandGroup(name='leveling', description='Leveling settings')

    @leveling_subcommand.command(name="list", description="List the leveling settings")
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @is_blocked()
    @analytics("leveling list")
    async def list_settings(self, ctx: discord.ApplicationContext):
        leveling_xp_multiplier = get_setting(ctx.guild.id, 'leveling_xp_multiplier', '1')
        weekend_event_enabled = get_setting(ctx.guild.id, 'weekend_event_enabled', 'false')
        weekend_event_multiplier = get_setting(ctx.guild.id, 'weekend_event_multiplier', '2')

        embed = discord.Embed(title='Leveling settings', color=discord.Color.blurple())
        embed.add_field(name='Leveling multiplier', value=f'`{leveling_xp_multiplier}x`')
        embed.add_field(name='Weekend event', value=weekend_event_enabled)
        embed.add_field(name='Weekend event multiplier', value=f'`{weekend_event_multiplier}x`')

        await ctx.respond(embed=embed, ephemeral=True)

    @leveling_subcommand.command(name='multiplier', description='Set the leveling multiplier')
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @discord.option(name="multiplier", description="The multiplier to set", type=int)
    @is_blocked()
    @analytics("leveling multiplier")
    async def set_multiplier(self, ctx: discord.ApplicationContext, multiplier: int):
        # Get old setting
        old_multiplier = get_setting(ctx.guild.id, 'leveling_xp_multiplier', str(multiplier))

        # Set new setting
        set_setting(ctx.guild.id, 'leveling_xp_multiplier', str(multiplier))

        # Create message
        logging_embed = discord.Embed(title="Leveling XP multiplier changed")
        logging_embed.add_field(name="User", value=f"{ctx.user.mention}")
        logging_embed.add_field(name="Multiplier", value=f"{old_multiplier} -> {str(multiplier)}")

        # Send to logs
        await log_into_logs(ctx.guild, logging_embed)

        # Send response
        await ctx.respond(f'Successfully set the leveling multiplier to {multiplier}.', ephemeral=True)

    @leveling_subcommand.command(name='weekend_event', description='Set the weekend event')
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @discord.option(name="enabled", description="Whether the weekend event is enabled", type=bool)
    @is_blocked()
    @analytics("leveling weekend event")
    async def set_weekend_event(self, ctx: discord.ApplicationContext, enabled: bool):
        # Get old setting
        old_weekend_event = get_setting(ctx.guild.id, "weekend_event_enabled", str(enabled).lower()) == "true"

        # Set setting
        set_setting(ctx.guild.id, 'weekend_event_enabled', str(enabled).lower())

        # Create message
        logging_embed = discord.Embed(title="Leveling XP weekend event changed")
        logging_embed.add_field(name="User", value=f"{ctx.user.mention}")
        logging_embed.add_field(name="Enabled", value="{old} -> {new}".format(old=("Enabled" if old_weekend_event else "Disabled"), new=("Enabled" if enabled else "Disabled")))
        
        # Send to logs
        await log_into_logs(ctx.guild, logging_embed)

        # Respond
        await ctx.respond(f'Successfully set the weekend event to {enabled}.', ephemeral=True)

    @leveling_subcommand.command(name='weekend_event_multiplier', description='Set the weekend event multiplier')
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @discord.option(name="weekend_event_multiplier", description="The multiplier to set", type=int)
    @is_blocked()
    @analytics("leveling weekend event multiplier")
    async def set_weekend_event_multiplier(self, ctx: discord.ApplicationContext, weekend_event_multiplier: int):
        old_setting = get_setting(ctx.guild.id, "weekend_event_multiplier", str(weekend_event_multiplier))

        set_setting(ctx.guild.id, 'weekend_event_multiplier', str(weekend_event_multiplier))

        # Create message
        logging_embed = discord.Embed(title="Leveling XP weekend event changed")
        logging_embed.add_field(name="User", value=f"{ctx.user.mention}")
        logging_embed.add_field(name="Multiplier", value=f"{old_setting} -> {str(weekend_event_multiplier)}")

        # Send to logs
        await log_into_logs(ctx.guild, logging_embed)

        # Respond
        await ctx.respond(f'Successfully set the weekend event multiplier to {weekend_event_multiplier}.',
                                        ephemeral=True)

    @leveling_subcommand.command(name='set_reward', description='Set a role for a level')
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @discord.option(name="level", description="The level to set the reward for", type=int)
    @discord.option(name='role', description='The role to set', type=discord.Role)
    @is_blocked()
    @analytics("leveling set reward")
    async def set_reward(self, ctx: discord.ApplicationContext, level: int, role: discord.Role):
        # Get old setting
        old_role_id = get_setting(ctx.guild.id, f"leveling_reward_{level}", '0')
        old_role = ctx.guild.get_role(int(old_role_id))

        # Set new setting
        set_setting(ctx.guild.id, f'leveling_reward_{level}', str(role.id))

        # Logging embed
        logging_embed = discord.Embed(title="Leveling reward added/changed")
        logging_embed.add_field(name="User", value=f"{ctx.user.mention}")
        if old_role_id == '0':
            logging_embed.add_field(name="Role", value=f"+Added: {role.mention}")
        else:
            logging_embed.add_field(name="Role", value=f"Changed: {old_role.mention if old_role is not None else old_role_id} -> {role.mention}")

        # Send into logs
        await log_into_logs(ctx.guild, logging_embed)

        # Send response
        await ctx.respond(f'Successfully set the reward for level {level} to {role.mention}.', ephemeral=True)

    @leveling_subcommand.command(name='remove_reward', description='Remove a role for a level')
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @discord.option(name="level", description="The level to remove the reward for", type=int)
    @is_blocked()
    @analytics("leveling remove reward")
    async def remove_reward(self, ctx: discord.ApplicationContext, level: int):
        # Get old setting
        old_role_id = get_setting(ctx.guild.id, f"leveling_reward_{level}", '0')
        old_role = ctx.guild.get_role(int(old_role_id))

        # Logging embed
        logging_embed = discord.Embed(title="Leveling reward added/changed")
        logging_embed.add_field(name="User", value=f"{ctx.user.mention}")
        if old_role is not None:
            logging_embed.add_field(name="Role", value=f"{old_role.mention}")
        else:
            logging_embed.add_field(name="Role", value="*Unknown*")
    
        # Send into logs
        await log_into_logs(ctx.guild, logging_embed)

        # Set new setting
        set_setting(ctx.guild.id, f'leveling_reward_{level}', '0')

        # Send response
        await ctx.respond(f'Successfully removed the reward for level {level}.', ephemeral=True)
