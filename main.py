import discord
import json
from features import welcoming, leveling, antiraid, chat_streaks
from discord.ext import commands as discord_commands_ext

with open('config.json', 'r', encoding='utf8') as f:
    data = json.load(f)

bot = discord.Bot(intents=discord.Intents.all())

@bot.event
async def on_application_command_error(ctx: discord.Interaction, error):
    if isinstance(error, discord_commands_ext.CommandOnCooldown):
        await ctx.response.send_message(f'Cooldown! Try again after {error.retry_after} seconds.', ephemeral=True)
        return
    
    if isinstance(error, discord_commands_ext.MissingPermissions):
        await ctx.response.send_message('You do not have the permissions to use this command. Missing: ' + ', '.join(error.missing_permissions), ephemeral=True)
        return
    
    if isinstance(error, discord_commands_ext.NoPrivateMessage):
        await ctx.response.send_message('This command cannot be used in private messages.', ephemeral=True)
        return

    raise error

bot.add_cog(welcoming.Welcoming(bot))
bot.add_cog(leveling.Leveling(bot))
bot.add_cog(antiraid.AntiRaid(bot))
bot.add_cog(chat_streaks.ChatStreaks(bot))

bot.run(data['token'])
