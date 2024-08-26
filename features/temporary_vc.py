import discord
from discord.ext import commands

from database import conn
from utils.languages import get_translation_for_key_localized as trl
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
            new_ch = await from_ch.guild.create_voice_channel(name=new_ch_name, reason=trl(0, for_user.guild.id, 'temporary_vc_mod_reason'), bitrate=from_ch.bitrate, user_limit=from_ch.user_limit)
        else:
            new_ch = await category.create_voice_channel(name=new_ch_name, reason=trl(0, for_user.guild.id, 'temporary_vc_mod_reason'), bitrate=from_ch.bitrate, user_limit=from_ch.user_limit)

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
                await member.move_to(vc, reason=trl(0, member.guild.id, 'temporary_vc_mod_reason'))

        # Now let's check leaving for temporary voice channel deletion

        if before.channel:
            if len(before.channel.voice_states) > 0:
                return

            cur = conn.cursor()
            cur.execute('select * from temporary_vcs where channel_id = ? and guild_id = ?', (before.channel.id, before.channel.guild.id))
            if cur.fetchone():
                await before.channel.delete(reason=trl(0, member.guild.id, 'temporary_vc_mod_reason'))

            cur.execute('delete from temporary_vcs where channel_id = ? and guild_id = ?', (before.channel.id, before.channel.guild.id))
            conn.commit()

    @temporary_vc_commands.command(name='add_creator_channel', description='Add a channel to create temporary voice channels')
    async def add_creator_channel(self, ctx: discord.ApplicationContext, channel: discord.VoiceChannel):
        cur = conn.cursor()
        cur.execute('insert into temporary_vc_creator_channels (id, channel_id, guild_id) values (?, ?, ?)', (ctx.author.id, channel.id, ctx.guild.id))
        conn.commit()
        await ctx.respond(trl(ctx.user.id, ctx.guild.id, 'temporary_vc_creator_channel_add').format(channel=channel.mention), ephemeral=True)

    @temporary_vc_commands.command(name='remove_creator_channel', description='Remove a channel to create temporary voice channels')
    async def remove_creator_channel(self, ctx: discord.ApplicationContext, channel: discord.VoiceChannel):
        cur = conn.cursor()
        cur.execute('select * from temporary_vc_creator_channels where channel_id = ? and guild_id = ?', (channel.id, ctx.guild.id))
        if not cur.fetchone():
            await ctx.respond(trl(ctx.user.id, ctx.guild.id, 'temporary_vc_error_channel_not_in_creator').format(channel=channel.mention), ephemeral=True)
            return

        cur.execute('delete from temporary_vc_creator_channels where channel_id = ? and guild_id = ?', (channel.id, ctx.guild.id))
        conn.commit()
        await ctx.respond(trl(ctx.user.id, ctx.guild.id, 'temporary_vc_creator_channel_remove').format(channel=channel.mention), ephemeral=True)

    @temporary_vc_commands.command(name='change_name', description='Change the name of a temporary voice channel')
    async def change_name(self, ctx: discord.ApplicationContext, name: str):
        if len(name) > 16:
            await ctx.respond(trl(ctx.user.id, ctx.guild.id, 'temporary_vc_error_name_too_long'), ephemeral=True)
            return

        if len(name) < 2:
            await ctx.respond(trl(ctx.user.id, ctx.guild.id, 'temporary_vc_error_name_too_short'), ephemeral=True)
            return

        cur = conn.cursor()
        cur.execute('select * from temporary_vcs where channel_id = ? and guild_id = ? and creator_id = ?', (ctx.channel.id, ctx.guild.id, ctx.user.id))
        if not cur.fetchone():
            await ctx.respond(trl(ctx.user.id, ctx.guild.id, 'temporary_vc_error_not_a_temporary_channel').format(channel=ctx.channel.mention), ephemeral=True)
            return

        await ctx.channel.edit(name=name)
        await ctx.respond(trl(ctx.user.id, ctx.guild.id, 'temporary_vc_name_change').format(channel=ctx.channel.mention, name=name), ephemeral=True)

    @temporary_vc_commands.command(name='change_max', description='Change the max users of a temporary voice channel')
    async def change_max(self, ctx: discord.ApplicationContext, max_users: int):
        if max_users < 2:
            await ctx.respond(trl(ctx.user.id, ctx.guild.id, 'temporary_vc_error_min_users'), ephemeral=True)
            return

        if max_users > 99:
            await ctx.respond(trl(ctx.user.id, ctx.guild.id, 'temporary_vc_error_max_users'), ephemeral=True)
            return

        cur = conn.cursor()
        cur.execute('select * from temporary_vcs where channel_id = ? and guild_id = ? and creator_id = ?', (ctx.channel.id, ctx.guild.id, ctx.user.id))
        if not cur.fetchone():
            await ctx.respond(trl(ctx.user.id, ctx.guild.id, 'temporary_vc_error_not_a_temporary_channel').format(channel=ctx.channel.mention), ephemeral=True)
            return

        await ctx.channel.edit(user_limit=max_users)
        await ctx.respond(trl(ctx.user.id, ctx.guild.id, 'temporary_vc_max_users_change').format(channel=ctx.channel.mention, max_users=str(max_users)), ephemeral=True)

    @temporary_vc_commands.command(name='change_bitrate', description='Change the bitrate of a temporary voice channel')
    async def change_bitrate(self, ctx: discord.ApplicationContext, bitrate: int):
        if bitrate < 8:
            await ctx.respond(trl(ctx.user.id, ctx.guild.id, 'temporary_vc_error_min_bitrate'), ephemeral=True)
            return

        if bitrate > 96:
            await ctx.respond(trl(ctx.user.id, ctx.guild.id, 'temporary_vc_error_max_bitrate'), ephemeral=True)
            return

        bitrate = bitrate * 1000

        cur = conn.cursor()
        cur.execute('select * from temporary_vcs where channel_id = ? and guild_id = ? and creator_id = ?', (ctx.channel.id, ctx.guild.id, ctx.user.id))
        if not cur.fetchone():
            await ctx.respond(trl(ctx.user.id, ctx.guild.id, 'temporary_vc_error_not_a_temporary_channel').format(channel=ctx.channel.mention), ephemeral=True)
            return

        await ctx.channel.edit(bitrate=bitrate)
        await ctx.respond(trl(ctx.user.id, ctx.guild.id, 'temporary_vc_bitrate_change').format(channel=ctx.channel.mention, bitrate=str(bitrate)), ephemeral=True)

    @temporary_vc_commands.command(name='change_default_name', description='Change the default name of a temporary voice channel. Use {name}, {username} and {guild} as placeholders')
    async def change_default_name(self, ctx: discord.ApplicationContext, name: str):
        set_setting(ctx.guild.id, 'temporary_vc_name', name)
        await ctx.respond(trl(ctx.user.id, ctx.guild.id, 'temporary_vc_name_format_change').format(name=name), ephemeral=True)
