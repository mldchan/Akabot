
import discord
import pymongo
from utils.settings import get_setting

class Welcoming(discord.Cog):
    def __init__(self, bot: discord.Bot, db: pymongo.MongoClient) -> None:
        self.bot = bot
        self.db = db
    
    @discord.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        target_channel_id = get_setting(self.db, member.guild.id, 'welcome_channel', '0')
        if target_channel_id == '0':
            return # The channel was not set and was initialised as we just ran this
        message_type = get_setting(self.db, member.guild.id, 'welcome_type', 'embed') # embed or text
        message_title = get_setting(self.db, member.guild.id, 'welcome_title', 'Welcome') # embed title (if type is embed)
        message_text = get_setting(self.db, member.guild.id, 'welcome_text', 'Welcome {user} to {server}!') # text of the message or description of embed

        target_channel = member.guild.get_channel(target_channel_id)
        if target_channel is None:
            return # Cannot find channel, don't do any further actions
        
        message_title = message_title.replace('{user}', member.display_name)
        message_title = message_title.replace('{server}', member.guild.name)
        message_title = message_title.replace('{memberCount}', member.guild.member_count)
        
        message_text = message_text.replace('{user}', member.display_name)
        message_text = message_text.replace('{server}', member.guild.name)
        message_text = message_text.replace('{memberCount}', member.guild.member_count)

        if message_type == 'embed':
            embed = discord.Embed(title=message_title, description=message_text) # Create the embed
            await target_channel.send(embed=embed) # Send it in the welcoming channel

    @discord.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        # TODO: Write this (duh)
        pass
