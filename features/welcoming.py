import discord
from discord.ext import commands as commands_ext

from utils.settings import get_setting, set_setting
from utils.blocked import is_blocked


class Welcoming(discord.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot

    @discord.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        target_channel_id = get_setting(member.guild.id, 'welcome_channel', '0')
        if target_channel_id == '0':
            return  # The channel was not set and was initialised as we just ran this
        message_type = get_setting(member.guild.id, 'welcome_type', 'embed')  # embed or text
        message_title = get_setting(member.guild.id, 'welcome_title', 'Welcome')  # embed title (if type is embed)
        message_text = get_setting(member.guild.id, 'welcome_text',
                                   'Welcome {user} to {server}!')  # text of the message or description of embed

        target_channel = member.guild.get_channel(int(target_channel_id))
        if target_channel is None:
            return  # Cannot find channel, don't do any further actions

        message_title = message_title.replace('{user}', member.display_name)
        message_title = message_title.replace('{server}', member.guild.name)
        message_title = message_title.replace('{memberCount}', str(member.guild.member_count))

        message_text = message_text.replace('{user}', member.display_name)
        message_text = message_text.replace('{server}', member.guild.name)
        message_text = message_text.replace('{memberCount}', str(member.guild.member_count))

        if message_type == 'embed':
            embed = discord.Embed(title=message_title, description=message_text)  # Create the embed
            await target_channel.send(embed=embed)  # Send it in the welcoming channel
        if message_type == 'text':
            await target_channel.send(content=message_text)  # Send it as text only

    @discord.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        target_channel_id = get_setting(member.guild.id, 'goodbye_channel', '0')
        if target_channel_id == '0':
            return  # The channel was not set and was initialised as we just ran this
        message_type = get_setting(member.guild.id, 'goodbye_type', 'embed')  # embed or text
        message_title = get_setting(member.guild.id, 'goodbye_title', 'Goodbye')  # embed title (if type is embed)
        message_text = get_setting(member.guild.id, 'goodbye_text',
                                   'Goodbye {user}!')  # text of the message or description of embed

        target_channel = member.guild.get_channel(int(target_channel_id))
        if target_channel is None:
            return  # Cannot find channel, don't do any further actions

        message_title = message_title.replace('{user}', member.display_name)
        message_title = message_title.replace('{server}', member.guild.name)
        message_title = message_title.replace('{memberCount}', str(member.guild.member_count))

        message_text = message_text.replace('{user}', member.display_name)
        message_text = message_text.replace('{server}', member.guild.name)
        message_text = message_text.replace('{memberCount}', str(member.guild.member_count))

        if message_type == 'embed':
            embed = discord.Embed(title=message_title, description=message_text)  # Create the embed
            await target_channel.send(embed=embed)  # Send it in the welcoming channel
        if message_type == 'text':
            await target_channel.send(content=message_text)  # Send it as text only

    welcome_subcommands = discord.SlashCommandGroup(name="welcome", description="Change the welcoming message")

    @welcome_subcommands.command(name="list", description="List the welcoming settings")
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @is_blocked()
    async def welcome_list_settings(self, ctx: discord.Interaction):
        welcome_channel = get_setting(ctx.guild.id, 'welcome_channel', '0')
        welcome_type = get_setting(ctx.guild.id, 'welcome_type', 'embed')
        welcome_title = get_setting(ctx.guild.id, 'welcome_title', 'Welcome')
        welcome_text = get_setting(ctx.guild.id, 'welcome_text', 'Welcome {user} to {server}!')

        embed = discord.Embed(title='Welcoming settings', color=discord.Color.blurple())
        embed.add_field(name='Welcoming channel', value=welcome_channel)
        embed.add_field(name='Welcoming message type', value=welcome_type)
        embed.add_field(name='Welcoming message title', value=welcome_title)
        embed.add_field(name='Welcoming message text', value=welcome_text)

        await ctx.response.send_message(embed=embed, ephemeral=True)

    @welcome_subcommands.command(name='channel', description="Set the welcoming channel")
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @is_blocked()
    async def welcome_channel(self, ctx: discord.Interaction, channel: discord.TextChannel):
        set_setting(ctx.guild.id, 'welcome_channel', str(channel.id))
        await ctx.response.send_message(f'Welcoming channel set to {channel.mention}!', ephemeral=True)

    @welcome_subcommands.command(name='type', description="Set whether you want to use message content or embed")
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @discord.option(name="message_type", description="The type of the message (embed or text)",
                    choices=['embed', 'text'])
    @is_blocked()
    async def welcome_type(self, ctx: discord.Interaction, message_type: str):
        set_setting(ctx.guild.id, 'welcome_type', message_type)
        await ctx.response.send_message(f'Welcoming message type set to {message_type}!', ephemeral=True)

    @welcome_subcommands.command(name='title', description="Set the title of the welcoming message")
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @discord.option(name="title", description="The title of the message")
    @is_blocked()
    async def welcome_title(self, ctx: discord.Interaction, title: str):
        set_setting(ctx.guild.id, 'welcome_title', title)
        await ctx.response.send_message(f'Welcoming message title set to {title}!', ephemeral=True)

    @welcome_subcommands.command(name='text', description="Set the text of the welcoming message")
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @discord.option(name="text", description="The content of the message or description of the embed")
    @is_blocked()
    async def welcome_text(self, ctx: discord.Interaction, text: str):
        set_setting(ctx.guild.id, 'welcome_text', text)
        await ctx.response.send_message(f'Welcoming message text set to {text}!', ephemeral=True)

    goodbye_subcommands = discord.SlashCommandGroup(name="goodbye", description="Change the goodbye message")

    @goodbye_subcommands.command(name="list", description="List the goodbye settings")
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @is_blocked()
    async def goodbye_list_settings(self, ctx: discord.Interaction):
        goodbye_channel = get_setting(ctx.guild.id, 'goodbye_channel', '0')
        goodbye_type = get_setting(ctx.guild.id, 'goodbye_type', 'embed')
        goodbye_title = get_setting(ctx.guild.id, 'goodbye_title', 'Welcome')
        goodbye_text = get_setting(ctx.guild.id, 'goodbye_text', 'Welcome {user} to {server}!')

        embed = discord.Embed(title='Goodbye settings', color=discord.Color.blurple())
        embed.add_field(name='Goodbye channel', value=goodbye_channel)
        embed.add_field(name='Goodbye message type', value=goodbye_type)
        embed.add_field(name='Goodbye message title', value=goodbye_title)
        embed.add_field(name='Goodbye message text', value=goodbye_text)

        await ctx.response.send_message(embed=embed, ephemeral=True)

    @goodbye_subcommands.command(name='channel', description="Set the goodbye channel")
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @is_blocked()
    async def goodbye_channel(self, ctx: discord.Interaction, channel: discord.TextChannel):
        set_setting(ctx.guild.id, 'goodbye_channel', str(channel.id))
        await ctx.response.send_message(f'Goodbye channel set to {channel.mention}!', ephemeral=True)

    @goodbye_subcommands.command(name='type', description="Set whether you want to use message content or embed")
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @discord.option(name="message_type", description="The type of the message (embed or text)",
                    choices=['embed', 'text'])
    @is_blocked()
    async def goodbye_type(self, ctx: discord.Interaction, message_type: str):
        set_setting(ctx.guild.id, 'goodbye_type', message_type)
        await ctx.response.send_message(f'Goodbye message type set to {message_type}!', ephemeral=True)

    @goodbye_subcommands.command(name='title', description="Set the title of the goodbye message")
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @discord.option(name="title", description="The title of the message")
    @is_blocked()
    async def goodbye_title(self, ctx: discord.Interaction, title: str):
        set_setting(ctx.guild.id, 'goodbye_title', title)
        await ctx.response.send_message(f'Goodbye message title set to {title}!', ephemeral=True)

    @goodbye_subcommands.command(name='text', description="Set the text of the goodbye message")
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @discord.option(name="text", description="The content of the message or description of the embed")
    @is_blocked()
    async def goodbye_text(self, ctx: discord.Interaction, text: str):
        set_setting(ctx.guild.id, 'goodbye_text', text)
        await ctx.response.send_message(f'Goodbye message text set to {text}!', ephemeral=True)
