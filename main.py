
import discord
import os
import logging
import pymongo
import bson
import json
from features import settings, welcoming
from discord.ext import commands as discord_commands_ext

with open('config.json', 'r') as f:
    data = json.load(f)

db_client = pymongo.MongoClient(data['conn_string'])

bot = discord.Bot()

@bot.event
async def on_application_command_error(ctx: discord.Interaction, error):
    if isinstance(error, discord_commands_ext.CommandOnCooldown):
        await ctx.response.send_message(f'Cooldown! Try again after {error.retry_after} seconds.')
        return
    
    if isinstance(error, discord_commands_ext.MissingPermissions):
        await ctx.response.send_message('You do not have the permissions to use this. Missing: ' + ', '.join(error.missing_permissions))
        return

    raise error

bot.add_cog(settings.Settings(bot, db_client))
bot.add_cog(welcoming.Welcoming(bot, db_client))

bot.run(data['token'])
