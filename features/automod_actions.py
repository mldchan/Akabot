
import datetime
import discord
from discord.ext import commands as discord_commands_ext
from database import conn
import logging

def db_init():
    cur = conn.cursor()
    cur.execute("create table if not exists automod_actions (guild_id bigint, rule_id bigint, rule_name text, action text)")
    cur.close()
    conn.commit()

def db_add_automod_action(guild_id: int, rule_id: int, rule_name: str, action: str):
    cur = conn.cursor()
    cur.execute("insert into automod_actions values (?, ?, ?, ?)", (guild_id, rule_id, rule_name, action))
    cur.close()
    conn.commit()

def db_remove_automod_action(guild_id: int, rule_id: int):
    cur = conn.cursor()
    cur.execute("delete from automod_actions where guild_id = ? and rule_id = ?", (guild_id, rule_id))
    cur.close()
    conn.commit()

def db_get_automod_action(guild_id: int, rule_id: int):
    cur = conn.cursor()
    cur.execute("select action from automod_actions where guild_id = ? and rule_id = ?", (guild_id, rule_id))
    action = cur.fetchone()
    cur.close()
    return action

def db_get_automod_actions(guild_id: int):
    cur = conn.cursor()
    cur.execute("select rule_id, rule_name, action from automod_actions where guild_id = ?", (guild_id,))
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
            logging.info("Automod action: {automod_action} {rule_id} {check}".format(automod_action=str(automod_action), rule_id=str(payload.rule_id), check=str(automod_action[0] == payload.rule_id)))
            if automod_action[0] == payload.rule_id:
                logging.info("Automod action triggered: {action}".format(action=automod_action[2]))
                if automod_action[2].startswith("timeout"):
                    if payload.member.timed_out:
                        return

                    duration = automod_action[2].split(" ")[1]
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
                    await payload.member.timeout_for(duration, reason="Automod action.")
                elif automod_action[2] == "ban":
                    logging.info("Banning member for {reason}".format(reason="Automod action."))
                    await payload.member.ban(reason="Automod action.")
                elif automod_action[2] == "kick":
                    logging.info("Kicking member for {reason}".format(reason="Automod action."))
                    await payload.member.kick(reason="Automod action.")

    automod_actions_subcommands = discord.SlashCommandGroup(name='automod_actions', description='Automod actions management.')

    @automod_actions_subcommands.command(name='add', description='Add an automod action.')
    @discord_commands_ext.bot_has_permissions(manage_guild=True)
    @discord_commands_ext.has_permissions(manage_messages=True)
    @discord.option(name="rule_name", description="Name of the rule, as it is in the settings.")
    @discord.option(name="action", description="Type of the action.", choices=["ban", "kick", "timeout 1h", "timeout 12h", "timeout 1d", "timeout 7d", "timeout 28d"])
    async def automod_actions_add(self, ctx: discord.ApplicationContext, rule_name: str, action: str):
        automod_actions = await ctx.guild.fetch_auto_moderation_rules()
        # verify rule exists and assign rule_id

        logging.info("Adding automod action: {rule_name} {action}".format(rule_name=rule_name, action=action))
        automod_rule = None
        for rule in automod_actions:
            if rule.name == rule_name:
                automod_rule = rule
                break

        logging.info("Found rule ID {automod_id} named {automod_name}".format(automod_id=automod_rule.id, automod_name=automod_rule.name))

        if not automod_rule:
            valid_rules = '\n'.join([f"{rule.name}: {rule.description}" for rule in automod_actions])
            await ctx.respond("Automod rule does not exist. Valid rules: {rules}".format(rules=valid_rules), ephemeral=True)
            return
        
        logging.info("Adding automod action({guild_id}, {rule_id}, {rule_name}, {action})".format(guild_id=ctx.guild.id, rule_id=automod_rule.id, rule_name=rule_name, action=action))
        db_add_automod_action(ctx.guild.id, automod_rule.id, rule_name, action)
        await ctx.respond("Automod action added.", ephemeral=True)

    @automod_actions_subcommands.command(name='remove', description='Remove an automod action.')
    @discord_commands_ext.bot_has_permissions(manage_guild=True)
    @discord_commands_ext.has_permissions(manage_messages=True)
    @discord.option(name="rule_name", description="Name of the rule, as it is in the settings.")
    async def automod_actions_remove(self, ctx: discord.ApplicationContext, rule_name: str):        
        # verify action exists, rule_name is NOT rule_id
        
        logging.info('Removing automod action: {rule_name}'.format(rule_name=rule_name))

        automod_actions = db_get_automod_actions(ctx.guild.id)
        automod_rule = None
        for rule in automod_actions:
            if rule[1] == rule_name:
                automod_rule = rule
                break

        logging.info("Found rule ID {automod_id} named {automod_name}".format(automod_id=automod_rule[0], automod_name=automod_rule[1]))

        if not automod_rule:
            await ctx.respond("Automod action does not exist.", ephemeral=True)
            return
        
        logging.info("Removing automod action({guild_id}, {rule_id})".format(guild_id=ctx.guild.id, rule_id=automod_rule[0]))
        db_remove_automod_action(ctx.guild.id, automod_rule[0])
        await ctx.respond("Automod action removed.", ephemeral=True)

    @automod_actions_subcommands.command(name='list', description='List automod actions.')
    @discord_commands_ext.bot_has_permissions(manage_guild=True)
    @discord_commands_ext.has_permissions(manage_messages=True)
    async def automod_actions_list(self, ctx: discord.ApplicationContext):
        automod_actions = db_get_automod_actions(ctx.guild.id)
        if not automod_actions:
            await ctx.respond("No automod actions.", ephemeral=True)
            return

        actions = '\n'.join([f"{action[1]}: {action[2]}" for action in automod_actions])
        await ctx.respond("Automod actions:\n{actions}".format(actions=actions), ephemeral=True)
