import json
import logging
import discord
from discord.ext import commands as discord_commands_ext

from features import welcoming, leveling, antiraid, chat_streaks, chat_revive, chat_summary, reaction_roles, \
    feedback_cmd, logging_mod, admin_cmds, giveaways, feedback_cmd
from utils.blocked import BlockedUserError, BlockedServerError

logger = logging.getLogger("Akatsuki")
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter("%(asctime)s | %(filename)s:%(lineno)d %(funcName)s %(name)s %(levelname)s | %(message)s"))
stream_handler.setLevel(logging.INFO)
logger.addHandler(stream_handler)
file_handler = logging.FileHandler("data/logs.log", encoding="utf8")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter("%(asctime)s | %(filename)s:%(lineno)d %(funcName)s %(name)s %(levelname)s | %(message)s"))
logger.addHandler(file_handler)

with open('config.json', 'r', encoding='utf8') as f:
    data = json.load(f)

intents = discord.Intents.default()
intents.members = True

bot = discord.Bot(intents=intents)


@bot.event
async def on_ready():
    print("temporary test")
    logger = logging.getLogger("Akatsuki")
    logger.info('Ready')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name="v3"))


@bot.event
async def on_application_command_error(ctx: discord.ApplicationContext, error):
    if isinstance(error, discord_commands_ext.CommandOnCooldown):
        await ctx.response.send_message(f'Cooldown! Try again after {error.retry_after} seconds.', ephemeral=True)
        return

    if isinstance(error, discord_commands_ext.MissingPermissions):
        await ctx.response.send_message(
            'You do not have the permissions to use this command. Missing: ' + ', '.join(error.missing_permissions),
            ephemeral=True)
        return

    if isinstance(error, discord_commands_ext.NoPrivateMessage):
        await ctx.response.send_message('This command cannot be used in private messages.', ephemeral=True)
        return

    if isinstance(error, discord_commands_ext.BotMissingPermissions):
        await ctx.response.send_message(
            f"The bot is missing permissions to perform this action.\n"
            f"Missing: {', '.join(error.missing_permissions)}",
            ephemeral=True)
        return

    if isinstance(error, BlockedUserError):
        await ctx.response.send_message(error.reason, ephemeral=True)
        return

    if isinstance(error, BlockedServerError):
        await ctx.response.send_message(error.reason, ephemeral=True)
        return

    raise error


if data["features"]["welcoming"]:
    logger.debug("Loading module Welcoming")
    bot.add_cog(welcoming.Welcoming(bot))

if data["features"]["leveling"]:
    logger.debug("Loading module Leveling")
    bot.add_cog(leveling.Leveling(bot))

if data["features"]["antiraid"]:
    logger.debug("Loading module AntiRaid")
    bot.add_cog(antiraid.AntiRaid(bot))

if data["features"]["chatstreaks"]:
    logger.debug("Loading module Chat Streaks")
    bot.add_cog(chat_streaks.ChatStreaks(bot))

if data["features"]["chatrevive"]:
    logger.debug("Loading module Chat Revive")
    bot.add_cog(chat_revive.ChatRevive(bot))

if data["features"]["chatsummary"]:
    logger.debug("Loading module Chat Summary")
    bot.add_cog(chat_summary.ChatSummary(bot))

if data["features"]["reactionroles"]:
    logger.debug("Loading module Reaction Roles")
    bot.add_cog(reaction_roles.ReactionRoles(bot))

if data["features"]["feedback"]:
    logger.debug("Loading module Feedback")
    bot.add_cog(feedback_cmd.SupportCmd(bot))

if data['features']['logging']:
    logger.debug("Loading module Logging")
    bot.add_cog(logging_mod.Logging(bot))

if data["features"]["admin_cmds"]:
    logger.debug("Loading module Admin Commands")
    bot.add_cog(admin_cmds.AdminCommands(bot))

if data["features"]["giveaways"]:
    logger.debug("Loading module Giveaways")
    bot.add_cog(giveaways.Giveaways(bot))

if data["features"]["support"]:
    logger.debug("Loading mudule SupportCMD")
    bot.add_cog(feedback_cmd.SupportCmd(bot))

bot.run(data['token'])
