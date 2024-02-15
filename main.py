import discord
import json
from features import welcoming, leveling
from discord.ext import commands as discord_commands_ext

with open('config.json', 'r', encoding='utf8') as f:
    data = json.load(f)

bot = discord.Bot(intents=discord.Intents.all())

@bot.event
async def on_application_command_error(ctx: discord.Interaction, error):
    if isinstance(error, discord_commands_ext.CommandOnCooldown):
        await ctx.response.send_message(f'Cooldown! Try again after {error.retry_after} seconds.')
        return
    
    if isinstance(error, discord_commands_ext.MissingPermissions):
        await ctx.response.send_message('You do not have the permissions to use this. Missing: ' + ', '.join(error.missing_permissions))
        return

    raise error

bot.add_cog(welcoming.Welcoming(bot))
bot.add_cog(leveling.Leveling(bot))

bot.run(data['token'])
