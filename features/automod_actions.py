
import datetime
import discord
from discord.ext import commands as discord_commands_ext
from database import conn
import logging

from utils.config import get_key
from utils.warning import add_warning

def db_init():
    cur = conn.cursor()
    cur.execute("create table if not exists automod_actions (id integer primary key autoincrement, guild_id bigint, rule_id bigint, rule_name text, action text, additional text)")
    cur.close()
    conn.commit()

def db_add_automod_action(guild_id: int, rule_id: int, rule_name: str, action: str, additional: str = "") -> int:
    cur = conn.cursor()
    cur.execute("insert into automod_actions(guild_id, rule_id, rule_name, action, additional) values (?, ?, ?, ?, ?)", (guild_id, rule_id, rule_name, action, additional))
    id = cur.lastrowid
    cur.close()
    conn.commit()
    return id

def db_remove_automod_action(id: int):
    cur = conn.cursor()
    cur.execute("delete from automod_actions where id = ?", (id,))
    cur.close()
    conn.commit()

def db_get_automod_actions(guild_id: int):
    cur = conn.cursor()
    cur.execute("select id, rule_id, rule_name, action, additional from automod_actions where guild_id = ?", (guild_id,))
    actions = cur.fetchall()
    cur.close()
    return actions

class AutomodActions(discord.Cog):
    def __init__(self, bot):
        self.bot = bot

        db_init()

    @discord.Cog.listener()
    async def on_auto_moderation_action_execution(self, payload: discord.AutoModActionExecutionEvent):
        automod_actions = db_get_automod_actions(payload.guild_id)
        for automod_action in automod_actions:
            logging.info("Automod action: {automod_action} {rule_id} {check}".format(automod_action=str(automod_action), rule_id=str(payload.rule_id), check=str(automod_action[1] == payload.rule_id)))
            if automod_action[1] == payload.rule_id:

                extra = str(automod_action[4]) # Autocompletion

                extra = extra.replace("{keyword}", payload.matched_keyword)
                extra = extra.replace("{name}", payload.member.display_name)
                extra = extra.replace("{guild}", payload.guild.name)

                logging.info("Automod action triggered: {action}".format(action=automod_action[3]))
                if automod_action[3].startswith("timeout"):
                    if payload.member.timed_out:
                        return

                    duration = automod_action[3].split(" ")[1]
                    if duration == "1h":
                        duration = datetime.timedelta(hours=1)
                    elif duration == "12h":
                        duration = datetime.timedelta(hours=12)
                    elif duration == "1d":
                        duration = datetime.timedelta(days=1)
                    elif duration == "7d":
                        duration = datetime.timedelta(days=7)
                    elif duration == "28d":
                        duration = datetime.timedelta(days=28)

                    logging.info("Timing out member for {duration}.".format(duration=duration.total_seconds()))
                    await payload.member.timeout_for(duration, reason=extra)
                elif automod_action[3] == "ban":
                    logging.info("Banning member for {reason}".format(reason=extra))
                    await payload.member.ban(reason=extra)
                elif automod_action[3] == "kick":
                    logging.info("Kicking member for {reason}".format(reason=extra))
                    await payload.member.kick(reason=extra)
                elif automod_action[3] == "DM":
                    logging.info("Sending DM about automod action to member for {reason}".format(reason=extra))
                    try:
                        await payload.member.send(extra)
                    except discord.Forbidden:
                        logging.info("Could not send DM to member.")
                elif automod_action[3] == "warning":
                    logging.info("Sending warning to member for {reason}".format(reason=extra))
                    await add_warning(payload.member, payload.guild, extra)


    automod_actions_subcommands = discord.SlashCommandGroup(name='automod_actions', description='Automod actions management.')

    @automod_actions_subcommands.command(name='add', description='Add an automod action.')
    @discord_commands_ext.bot_has_permissions(manage_guild=True)
    @discord_commands_ext.has_permissions(manage_messages=True)
    @discord.option(name="rule_name", description="Name of the rule, as it is in the settings.")
    @discord.option(name="action", description="Type of the action.", choices=["ban", "kick", "timeout 1h", "timeout 12h", "timeout 1d", "timeout 7d", "timeout 28d", "DM", "warning"])
    @discord.option(name="message_reason", description="Reason for the action / Message for DM.")
    async def automod_actions_add(self, ctx: discord.ApplicationContext, rule_name: str, action: str, message_reason: str = None):
        # verify count of rules
        automod_db_actions = db_get_automod_actions(ctx.guild.id)
        if len(automod_db_actions) >= int(get_key("AutomodActions_MaxActions", "5")):
            await ctx.respond("You have reached the maximum number of automod actions.", ephemeral=True)
            return

        automod_actions = await ctx.guild.fetch_auto_moderation_rules()
        # verify rule exists and assign rule_id

        logging.info("Adding automod action: {rule_name} {action}".format(rule_name=rule_name, action=action))
        automod_rule = None
        for rule in automod_actions:
            if rule.name == rule_name:
                automod_rule = rule
                break

        if not automod_rule:
            valid_rules = '\n'.join([f"{rule.name}" for rule in automod_actions])
            await ctx.respond("Automod rule does not exist. Valid rules: {rules}".format(rules=valid_rules), ephemeral=True)
            return

        logging.info("Found rule ID {automod_id} named {automod_name}".format(automod_id=automod_rule.id, automod_name=automod_rule.name))

        # Check if there's already a timeout action
        for action in automod_db_actions:
            if action[1] == automod_rule.id and action[3] == action:
                await ctx.respond("There's already an action for this rule.", ephemeral=True)
                return

            if action[1] == automod_rule.id and action[3].startswith("timeout") and action.startswith("timeout"):
                await ctx.respond("There's already a timeout action for this rule.", ephemeral=True)
                return

        # Determine message if not specified
        if action == "DM" and not message_reason:
            message_reason = "Your message was flagged and hidden by the Discord auto-moderation system. The keyword that triggered this action was: `{keyword}`. Please refrain from using this keyword in the future again."
        elif not message_reason:
            message_reason = "Akabot automod actions action"

        logging.info("Adding automod action({guild_id}, {rule_id}, {rule_name}, {action})".format(guild_id=ctx.guild.id, rule_id=automod_rule.id, rule_name=rule_name, action=action))
        id = db_add_automod_action(ctx.guild.id, automod_rule.id, rule_name, action, additional=message_reason)
        await ctx.respond("Automod action added. It's ID is {id}".format(id=id), ephemeral=True)

    @automod_actions_subcommands.command(name='remove', description='Remove an automod action.')
    @discord_commands_ext.bot_has_permissions(manage_guild=True)
    @discord_commands_ext.has_permissions(manage_messages=True)
    @discord.option(name="rule_name", description="Name of the rule, as it is in the settings.")
    async def automod_actions_remove(self, ctx: discord.ApplicationContext, id: int):
        # verify action exists, rule_name is NOT rule_id

        logging.info('Verifying automod action with ID {id} exists'.format(id=str(id)))

        automod_actions = db_get_automod_actions(ctx.guild.id)
        automod_rule = None
        for rule in automod_actions:
            if rule[0] == id:
                automod_rule = rule
                break

        logging.info("Found rule ID {automod_id} named {automod_name}".format(automod_id=automod_rule[0], automod_name=automod_rule[1]))

        if not automod_rule:
            await ctx.respond("Automod action does not exist.", ephemeral=True)
            return

        logging.info("Removing automod action({rule_id})".format(rule_id=str(automod_rule[0])))
        db_remove_automod_action(id)
        await ctx.respond("Automod action removed.", ephemeral=True)

    @automod_actions_subcommands.command(name='list', description='List automod actions.')
    @discord_commands_ext.bot_has_permissions(manage_guild=True)
    @discord_commands_ext.has_permissions(manage_messages=True)
    async def automod_actions_list(self, ctx: discord.ApplicationContext):
        automod_actions = db_get_automod_actions(ctx.guild.id)
        if not automod_actions:
            await ctx.respond("No automod actions.", ephemeral=True)
            return

        actions = '\n'.join([f"`{action[0]}`: {action[2]}: {action[3]}" for action in automod_actions])
        await ctx.respond("Automod actions:\n{actions}".format(actions=actions), ephemeral=True)
