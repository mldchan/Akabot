
import discord
import os
import logging
import pymongo
import bson
import json
from features import settings, welcoming

with open('config.json', 'r') as f:
    data = json.load(f)

db_client = pymongo.MongoClient(data['conn_string'])

bot = discord.Bot()

bot.add_cog(settings.Settings(bot, db_client))
bot.add_cog(welcoming.Welcoming(bot, db_client))

bot.run(data['token'])
