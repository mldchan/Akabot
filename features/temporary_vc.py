import discord

from database import conn
from utils.settings import get_setting, set_setting


class TemporaryVC(discord.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

        cur = conn.cursor()
        cur.execute('create table if not exists temporary_vc_creator_channels (id integer primary key autoincrement, channel_id bigint, guild_id bigint)')
        cur.execute('create table if not exists temporary_vcs (id integer primary key autoincrement, channel_id bigint, guild_id bigint, creator_id bigint)')

    temporary_vc_commands = discord.SlashCommandGroup(name='temporary_voice_channels', description='Temporary VC channels commands')

    async def new_temporary_channel(self, from_ch: discord.VoiceChannel, for_user: discord.Member) -> discord.VoiceChannel:
        category = from_ch.category

        new_ch_name = get_setting(for_user.guild.id, 'temporary_vc_name', '{name}\'s channel')

        new_ch_name = new_ch_name.replace('{name}', for_user.display_name)
        new_ch_name = new_ch_name.replace('{username}', for_user.name)
        new_ch_name = new_ch_name.replace('{guild}', for_user.guild.name)

        if not category:
            new_ch = await from_ch.guild.create_voice_channel(name=new_ch_name, reason='Temporary voice channels', bitrate=from_ch.bitrate, user_limit=from_ch.user_limit)
        else:
            new_ch = await category.create_voice_channel(name=new_ch_name, reason='Temporary voice channels', bitrate=from_ch.bitrate, user_limit=from_ch.user_limit)

        cur = conn.cursor()
        cur.execute('insert into temporary_vcs (channel_id, guild_id, creator_id) values (?, ?, ?)', (new_ch.id, new_ch.guild.id, for_user.id))
        conn.commit()

        if '{id}' in new_ch_name:
            id = cur.lastrowid
            new_ch_name = new_ch_name.replace('{id}', str(id))
            await new_ch.edit(name=new_ch_name)

        return new_ch

    @discord.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        # First let's check joining for temporary voice channel creation

        if after.channel:
            cur = conn.cursor()
            cur.execute('select * from temporary_vc_creator_channels where channel_id = ? and guild_id = ?', (after.channel.id, after.channel.guild.id))
            if cur.fetchone():
                vc = await self.new_temporary_channel(after.channel, member)
                await member.move_to(vc, reason='Temporary voice channels')

        # Now let's check leaving for temporary voice channel deletion

        if before.channel:
            if len(before.channel.voice_states) > 0:
                return

            cur = conn.cursor()
            cur.execute('select * from temporary_vcs where channel_id = ? and guild_id = ?', (before.channel.id, before.channel.guild.id))
            if cur.fetchone():
                await before.channel.delete(reason='Temporary voice channels')

            cur.execute('delete from temporary_vcs where channel_id = ? and guild_id = ?', (before.channel.id, before.channel.guild.id))
            conn.commit()

    @temporary_vc_commands.command(name='add_creator_channel', description='Add a channel to create temporary voice channels')
    async def add_creator_channel(self, ctx: discord.ApplicationContext, channel: discord.VoiceChannel):
        cur = conn.cursor()
        cur.execute('insert into temporary_vc_creator_channels (id, channel_id, guild_id) values (?, ?, ?)', (ctx.author.id, channel.id, ctx.guild.id))
        conn.commit()
        await ctx.respond(f'Channel {channel.mention} added to create temporary voice channels', ephemeral=True)

    @temporary_vc_commands.command(name='remove_creator_channel', description='Remove a channel to create temporary voice channels')
    async def remove_creator_channel(self, ctx: discord.ApplicationContext, channel: discord.VoiceChannel):
        cur = conn.cursor()
        cur.execute('select * from temporary_vc_creator_channels where channel_id = ? and guild_id = ?', (channel.id, ctx.guild.id))
        if not cur.fetchone():
            await ctx.respond(f'Channel {channel.mention} is not in the list of creating temporary voice channels', ephemeral=True)
            return

        cur.execute('delete from temporary_vc_creator_channels where channel_id = ? and guild_id = ?', (channel.id, ctx.guild.id))
        conn.commit()
        await ctx.respond(f'Channel {channel.mention} removed from creating temporary voice channels', ephemeral=True)

    @temporary_vc_commands.command(name='change_name', description='Change the name of a temporary voice channel')
    async def change_name(self, ctx: discord.ApplicationContext, name: str):
        cur = conn.cursor()
        cur.execute('select * from temporary_vcs where channel_id = ? and guild_id = ? and creator_id = ?', (ctx.channel.id, ctx.guild.id, ctx.user.id))
        if not cur.fetchone():
            await ctx.respond(f'Channel {ctx.channel.mention} is not a temporary voice channel', ephemeral=True)
            return

        await ctx.channel.edit(name=name)
        await ctx.respond(f'Name of channel {ctx.channel.mention} changed to {name}', ephemeral=True)

    @temporary_vc_commands.command(name='change_max', description='Change the max users of a temporary voice channel')
    async def change_max(self, ctx: discord.ApplicationContext, max_users: int):
        cur = conn.cursor()
        cur.execute('select * from temporary_vcs where channel_id = ? and guild_id = ? and creator_id = ?', (ctx.channel.id, ctx.guild.id, ctx.user.id))
        if not cur.fetchone():
            await ctx.respond(f'Channel {ctx.channel.mention} is not a temporary voice channel', ephemeral=True)
            return

        await ctx.channel.edit(user_limit=max_users)
        await ctx.respond(f'Max users of channel {ctx.channel.mention} changed to {max_users}', ephemeral=True)

    @temporary_vc_commands.command(name='change_bitrate', description='Change the bitrate of a temporary voice channel')
    async def change_bitrate(self, ctx: discord.ApplicationContext, bitrate: int):
        cur = conn.cursor()
        cur.execute('select * from temporary_vcs where channel_id = ? and guild_id = ? and creator_id = ?', (ctx.channel.id, ctx.guild.id, ctx.user.id))
        if not cur.fetchone():
            await ctx.respond(f'Channel {ctx.channel.mention} is not a temporary voice channel', ephemeral=True)
            return

        await ctx.channel.edit(bitrate=bitrate)
        await ctx.respond(f'Bitrate of channel {ctx.channel.mention} changed to {bitrate}', ephemeral=True)

    @temporary_vc_commands.command(name='change_default_name', description='Change the default name of a temporary voice channel')
    async def change_default_name(self, ctx: discord.ApplicationContext, name: str):
        set_setting(ctx.guild.id, 'temporary_vc_name', name)
        await ctx.respond(f'Default name of temporary voice channels changed to {name}', ephemeral=True)
