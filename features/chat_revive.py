import time

import discord
from discord.ext import commands as commands_ext
from discord.ext import tasks

from database import conn as db
from utils.analytics import analytics
from utils.blocked import is_blocked


class ChatRevive(discord.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

        cur = db.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS chat_revive (guild_id INTEGER, channel_id INTEGER, role_id INTEGER, revival_time INTEGER, last_message DATETIME, revived BOOLEAN)")
        cur.close()
        db.commit()

    @discord.Cog.listener()
    @is_blocked()
    async def on_ready(self):
        self.revive_channels.start()

    @discord.Cog.listener()
    @is_blocked()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        cur = db.cursor()
        cur.execute('UPDATE chat_revive SET last_message = ?, revived = ? WHERE guild_id = ? AND channel_id = ?',
                    (time.time(), False, message.guild.id, message.channel.id))
        cur.close()
        db.commit()

    @tasks.loop(minutes=1)
    async def revive_channels(self):
        for guild in self.bot.guilds:
            cur = db.cursor()
            cur.execute('SELECT * FROM chat_revive WHERE guild_id = ?', (guild.id,))
            settings = cur.fetchall()
            for revive_channel in settings:
                if revive_channel[5]:
                    continue

                if time.time() - revive_channel[4] > revive_channel[3]:
                    role = guild.get_role(revive_channel[2])
                    if role is None:
                        continue

                    channel = guild.get_channel(revive_channel[1])
                    if channel is None:
                        continue
                    await channel.send(f'{role.mention}, this channel has been inactive for a while.')
                    cur.execute('UPDATE chat_revive SET revived = ? WHERE guild_id = ? AND channel_id = ?',
                                (True, guild.id, revive_channel[1]))

            cur.close()
            db.commit()

    chat_revive_subcommand = discord.SlashCommandGroup(name='chatrevive', description='Revive channels')

    @chat_revive_subcommand.command(name="set", description="Set revive settings for a channel")
    @commands_ext.guild_only()
    @commands_ext.has_permissions(manage_guild=True)
    @is_blocked()
    @analytics("chatrevive set")
    async def set_revive_settings(self, ctx: discord.ApplicationContext, channel: discord.TextChannel, revival_minutes: int,
                                  revival_role: discord.Role):
        cur = db.cursor()
        cur.execute('DELETE FROM chat_revive WHERE guild_id = ? AND channel_id = ?', (ctx.guild.id, channel.id))
        cur.execute(
            'INSERT INTO chat_revive (guild_id, channel_id, role_id, revival_time, last_message, revived) VALUES (?, ?, ?, ?, ?, ?)',
            (ctx.guild.id, channel.id, revival_role.id, revival_minutes * 60, time.time(), False))
        cur.close()
        db.commit()
        await ctx.response.send_message(f'Successfully set revive settings for {channel.mention}.', ephemeral=True)

    @chat_revive_subcommand.command(name="remove", description="List the revive settings")
    @commands_ext.guild_only()
    @commands_ext.has_permissions(manage_guild=True)
    @is_blocked()
    @analytics("chatrevive remove")
    async def remove_revive_settings(self, ctx: discord.ApplicationContext, channel: discord.TextChannel):
        cur = db.cursor()
        cur.execute('DELETE FROM chat_revive WHERE guild_id = ? AND channel_id = ?', (ctx.guild.id, channel.id))
        cur.close()
        db.commit()
        await ctx.response.send_message(f'Successfully removed revive settings for {channel.mention}.', ephemeral=True)

    @chat_revive_subcommand.command(name="list", description="List the revive settings")
    @commands_ext.guild_only()
    @commands_ext.has_permissions(manage_guild=True)
    @is_blocked()
    @analytics("chatrevive list")
    async def list_revive_settings(self, ctx: discord.ApplicationContext, channel: discord.TextChannel):
        cur = db.cursor()
        cur.execute('SELECT role_id, revival_time FROM chat_revive WHERE guild_id = ? AND channel_id = ?',
                    (ctx.guild.id, channel.id))
        result = cur.fetchone()

        if not result:
            await ctx.response.send_message(f'There are no revive settings for {channel.mention}.', ephemeral=True)
            return

        role_id, revival_time = result
        role = ctx.guild.get_role(role_id)

        embed = discord.Embed(title=f'Revive settings for {channel.name}', color=discord.Color.blurple())
        embed.add_field(name='Role', value=role.mention)
        embed.add_field(name='Revival time (seconds)', value=revival_time)

        await ctx.response.send_message(embed=embed, ephemeral=True)
