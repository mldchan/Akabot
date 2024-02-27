import json

import discord
from discord.ext import commands as discord_commands_ext

from features import welcoming, leveling, antiraid, chat_streaks, chat_revive, chat_summary, reaction_roles, polls, feedback_cmd
from utils.blocked import BlockedUserError, BlockedServerError

with open('config.json', 'r', encoding='utf8') as f:
    data = json.load(f)

bot = discord.Bot(intents=discord.Intents.all())


@bot.event
async def on_application_command_error(ctx: discord.Interaction, error):
    if isinstance(error, discord_commands_ext.CommandOnCooldown):
        await ctx.response.send_message(f'Cooldown! Try again after {error.retry_after} seconds.', ephemeral=True)
        return

    if isinstance(error, discord_commands_ext.MissingPermissions):
        await ctx.response.send_message(
            'You do not have the permissions to use this command. Missing: ' +
            ', '.join(error.missing_permissions),
            ephemeral=True)
        return

    if isinstance(error, discord_commands_ext.NoPrivateMessage):
        await ctx.response.send_message('This command cannot be used in private messages.', ephemeral=True)
        return

    if isinstance(error, BlockedUserError):
        await ctx.response.send_message(error.reason, ephemeral=True)
        return

    if isinstance(error, BlockedServerError):
        await ctx.response.send_message(error.reason, ephemeral=True)
        return

    raise error


if (data["features"]["welcoming"]):
    bot.add_cog(welcoming.Welcoming(bot))

if (data["features"]["leveling"]):
    bot.add_cog(leveling.Leveling(bot))

if (data["features"]["antiraid"]):
    bot.add_cog(antiraid.AntiRaid(bot))

if (data["features"]["chatstreaks"]):
    bot.add_cog(chat_streaks.ChatStreaks(bot))

if (data["features"]["chatrevive"]):
    bot.add_cog(chat_revive.ChatRevive(bot))

if (data["features"]["chatsummary"]):
    bot.add_cog(chat_summary.ChatSummary(bot))

if (data["features"]["reactionroles"]):
    bot.add_cog(reaction_roles.ReactionRoles(bot))

if (data["features"]["polls"]):
    bot.add_cog(polls.Polls(bot))

if (data["features"]["feedback"]):
    bot.add_cog(feedback_cmd.SupportCmd(bot))

bot.run(data['token'])
