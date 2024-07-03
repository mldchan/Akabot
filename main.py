import json
import discord
from discord.ext import commands as discord_commands_ext

from features import welcoming, leveling, antiraid, chat_streaks, chat_revive, chat_summary, reaction_roles, \
    logging_mod, admin_cmds, giveaways, feedback_cmd, moderation, cleanup_task, verification, velky_stompies, \
    roles_on_join, heartbeat
from utils.blocked import BlockedUserError, BlockedServerError
import sentry_sdk
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

BOT_VERSION = "3.12"

with open('config.json', 'r', encoding='utf8') as f:
    data = json.load(f)

if 'sentry' in data and data['sentry']['enabled']:
    sentry_sdk.init(data['sentry']['dsn'])

intents = discord.Intents.default()
intents.members = True

bot = discord.Bot(intents=intents)


@bot.event
async def on_ready():
    bot.add_view(verification.VerificationView())
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name=f"v{BOT_VERSION}"))


@bot.event
async def on_application_command_error(ctx: discord.ApplicationContext, error):
    if isinstance(error, discord_commands_ext.CommandOnCooldown):
        minutes = int(error.retry_after / 60)
        seconds = int(error.retry_after % 60)
        if minutes > 0:
            await ctx.respond(f'Cooldown! Try again after {minutes} minutes and {seconds} seconds.', ephemeral=True)
        else:
            await ctx.respond(f'Cooldown! Try again after {seconds} seconds.', ephemeral=True)
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
    
    sentry_sdk.capture_exception(error)
    raise error

bot.add_cog(cleanup_task.DbCleanupTask())
bot.add_cog(welcoming.Welcoming(bot))
bot.add_cog(leveling.Leveling(bot))
bot.add_cog(antiraid.AntiRaid(bot))
bot.add_cog(chat_streaks.ChatStreaks(bot))
bot.add_cog(chat_revive.ChatRevive(bot))
bot.add_cog(chat_summary.ChatSummary(bot))
bot.add_cog(reaction_roles.ReactionRoles(bot))
bot.add_cog(feedback_cmd.SupportCmd(bot, gh_info=data["github"]))
bot.add_cog(logging_mod.Logging(bot))
bot.add_cog(admin_cmds.AdminCommands(bot))
bot.add_cog(giveaways.Giveaways(bot))
bot.add_cog(moderation.Moderation(bot))
bot.add_cog(verification.Verification(bot))
bot.add_cog(velky_stompies.VelkyStompies())
bot.add_cog(roles_on_join.RolesOnJoin(bot))
bot.add_cog(heartbeat.Heartbeat(heartbeat.HeartbeatData(**data["heartbeat"])))

bot.run(data['token'])
