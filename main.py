import json
import logging
import discord
from discord.ext import commands as discord_commands_ext

from features import welcoming, leveling, antiraid, chat_streaks, chat_revive, chat_summary, reaction_roles, \
    feedback_cmd, logging_mod, admin_cmds, giveaways, feedback_cmd, moderation, cleanup_task, verification, velky_stompies
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

BOT_VERSION = "3.1"

with open('config.json', 'r', encoding='utf8') as f:
    data = json.load(f)

intents = discord.Intents.default()
intents.members = True

bot = discord.Bot(intents=intents)


@bot.event
async def on_ready():
    bot.add_view(verification.VerificationView())
    logger = logging.getLogger("Akatsuki")
    logger.info('Ready')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name=f"v{BOT_VERSION}"))


@bot.event
async def on_application_command_error(ctx: discord.ApplicationContext, error):
    logging.warning(error)

    if isinstance(error, discord_commands_ext.CommandOnCooldown):
        await ctx.respond(f'Cooldown! Try again after {error.retry_after} seconds.', ephemeral=True)
        return

    if isinstance(error, discord_commands_ext.MissingPermissions):
        await ctx.respond(
            'You do not have the permissions to use this command. Missing: ' + ', '.join(error.missing_permissions),
            ephemeral=True)
        return

    if isinstance(error, discord_commands_ext.NoPrivateMessage):
        await ctx.respond('This command cannot be used in private messages.', ephemeral=True)
        return

    if isinstance(error, discord_commands_ext.BotMissingPermissions):
        await ctx.respond(
            f"The bot is missing permissions to perform this action.\n"
            f"Missing: {', '.join(error.missing_permissions)}",
            ephemeral=True)
        return

    if isinstance(error, BlockedUserError):
        await ctx.respond(error.reason, ephemeral=True)
        return

    if isinstance(error, BlockedServerError):
        await ctx.respond(error.reason, ephemeral=True)
        return


bot.add_cog(cleanup_task.DbCleanupTask())
bot.add_cog(welcoming.Welcoming(bot))
bot.add_cog(leveling.Leveling(bot))
bot.add_cog(antiraid.AntiRaid(bot))
bot.add_cog(chat_streaks.ChatStreaks(bot))
bot.add_cog(chat_revive.ChatRevive(bot))
bot.add_cog(chat_summary.ChatSummary(bot))
bot.add_cog(reaction_roles.ReactionRoles(bot))
bot.add_cog(feedback_cmd.SupportCmd(bot))
bot.add_cog(logging_mod.Logging(bot))
bot.add_cog(admin_cmds.AdminCommands(bot))
bot.add_cog(giveaways.Giveaways(bot))
bot.add_cog(moderation.Moderation(bot))
bot.add_cog(verification.Verification(bot))
bot.add_cog(velky_stompies.VelkyStompies())

bot.run(data['token'])
