import logging

import discord
import sentry_sdk
from discord.ext import commands as discord_commands_ext
from sentry_sdk.integrations.logging import LoggingIntegration

from features import welcoming, leveling, antiraid, chat_streaks, chat_revive, chat_summary, reaction_roles, \
    logging_mod, admin_cmds, giveaways, feedback_cmd, moderation, cleanup_task, verification, velky_stompies, \
    roles_on_join, heartbeat, automod_actions, power_outage_announcement, per_user_settings, server_settings, \
    bot_help, announcement_channels, tickets, debug_commands, birthday_announcements, send_server_count, \
    suggestions, temporary_vc
from utils.config import get_key
from utils.languages import get_translation_for_key_localized as trl

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logging.captureWarnings(True)

BOT_VERSION = get_key("Bot_Version", "3.2")

if get_key("Sentry_Enabled", "false") == "true":
    sentry_sdk.init(get_key("Sentry_DSN"),
                    integrations=[LoggingIntegration(level=logging.INFO, event_level=logging.WARN)],
                    traces_sample_rate=1.0,
                    profiles_sample_rate=1.0)

intents = discord.Intents.default()
intents.members = True

bot = discord.Bot(intents=intents)


@bot.event
async def on_ready():
    bot.add_view(verification.VerificationView())
    bot.add_view(tickets.TicketCreateView(""))
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name=f"v{BOT_VERSION}"))


@bot.event
async def on_application_command_error(ctx: discord.ApplicationContext, error):
    if isinstance(error, discord_commands_ext.CommandOnCooldown):
        minutes = int(error.retry_after / 60)
        seconds = int(error.retry_after % 60)
        if minutes > 0:
            await ctx.respond(
                trl(ctx.user.id, ctx.guild.id, "cooldown_2").format(minutes=str(minutes), seconds=str(seconds)),
                ephemeral=True)
        else:
            await ctx.respond(trl(ctx.user.id, ctx.guild.id, "cooldown_1").format(seconds=str(seconds)), ephemeral=True)
        return

    if isinstance(error, discord_commands_ext.MissingPermissions):
        await ctx.respond(
            trl(ctx.user.id, ctx.guild.id, "command_no_permission").format(
                permissions=', '.join(error.missing_permissions)),
            ephemeral=True)
        return

    if isinstance(error, discord_commands_ext.NoPrivateMessage):
        await ctx.respond(trl(ctx.user.id, ctx.guild.id, "command_no_private"), ephemeral=True)
        return

    if isinstance(error, discord_commands_ext.BotMissingPermissions):
        await ctx.respond(trl(ctx.user.id, ctx.guild.id, "command_bot_no_perm").format(
            permissions=', '.join(error.missing_permissions)),
                          ephemeral=True)
        return

    sentry_sdk.capture_exception(error)
    try:
        # respond
        await ctx.respond(trl(ctx.user.id, ctx.guild.id, "command_error_generic"), ephemeral=True)
    except Exception:
        print("Failed to respond")
    raise error


if get_key("Feature_DatabaseCleanupTask", "true") == "true":
    bot.add_cog(cleanup_task.DbCleanupTask())
if get_key("Feature_WelcomeGoodbye", "true") == "true":
    bot.add_cog(welcoming.Welcoming(bot))
if get_key("Feature_Leveling", "true") == "true":
    bot.add_cog(leveling.Leveling(bot))
if get_key("Feature_AntiRaid", "true") == "true":
    bot.add_cog(antiraid.AntiRaid(bot))
if get_key("Feature_ChatStreaks", "true") == "true":
    bot.add_cog(chat_streaks.ChatStreaks(bot))
if get_key("Feature_ChatRevive", "true") == "true":
    bot.add_cog(chat_revive.ChatRevive(bot))
if get_key("Feature_ChatSummary", "true") == "true":
    bot.add_cog(chat_summary.ChatSummary(bot))
if get_key("Feature_ReactionRoles", "true") == "true":
    bot.add_cog(reaction_roles.ReactionRoles(bot))
if get_key("Feature_Logging", "true") == "true":
    bot.add_cog(logging_mod.Logging(bot))
if get_key("Feature_AdminCommands", "true") == "true":
    bot.add_cog(admin_cmds.AdminCommands(bot))
if get_key("Feature_Giveaways", "true") == "true":
    bot.add_cog(giveaways.Giveaways(bot))
if get_key("Feature_FeedbackCmd", "true") == "true":
    bot.add_cog(feedback_cmd.SupportCmd(bot))
if get_key("Feature_Moderation", "true") == "true":
    bot.add_cog(moderation.Moderation(bot))
if get_key("Feature_Verification", "true") == "true":
    bot.add_cog(verification.Verification(bot))
if get_key("Feature_VelkyStompies", "true") == "true":
    bot.add_cog(velky_stompies.VelkyStompies())
if get_key("Feature_RolesOnJoin", "true") == "true":
    bot.add_cog(roles_on_join.RolesOnJoin(bot))
if get_key("Feature_Heartbeat", "true") == "true":
    bot.add_cog(heartbeat.Heartbeat())
if get_key("Feature_AutomodActions", "true") == "true":
    bot.add_cog(automod_actions.AutomodActions(bot))
if get_key("PowerOutageAnnouncements_Enabled", "false") == "true":
    bot.add_cog(power_outage_announcement.PowerOutageAnnouncement(bot))
if get_key("PerUserSettings_Enabled", "true") == "true":
    bot.add_cog(per_user_settings.PerUserSettings(bot))
if get_key("Feature_ServerSettings", "true") == "true":
    bot.add_cog(server_settings.ServerSettings())
if get_key("Feature_HelpCommands", "true") == "true":
    bot.add_cog(bot_help.Help(bot))
if get_key("Feature_AnnouncementChannels", "true") == "true":
    bot.add_cog(announcement_channels.AnnouncementChannels(bot))
if get_key("Feature_Tickets", "true") == "true":
    bot.add_cog(tickets.Tickets(bot))
if get_key("Feature_DebugCommands", "false") == "true":
    bot.add_cog(debug_commands.DebugCommands(bot))
if get_key("Feature_BirthdayAnnouncements", "true") == "true":
    bot.add_cog(birthday_announcements.BirthdayAnnouncements(bot))
bot.add_cog(send_server_count.SendServerCount(bot))
if get_key("Feature_SuggestionsEnabled", "true") == "true":
    bot.add_cog(suggestions.Suggestions(bot))
if get_key('Feature_TemporaryVC', 'true') == 'true':
    bot.add_cog(temporary_vc.TemporaryVC(bot))

bot.run(get_key("Bot_Token"))
