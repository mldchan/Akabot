import discord
from discord.ext import commands as commands_ext

from utils.analytics import analytics
from utils.languages import get_translation_for_key_localized as trl
from utils.logging_util import log_into_logs
from utils.settings import get_setting, set_setting


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
        message_title = message_title.replace('{mention}', member.mention)

        message_text = message_text.replace('{user}', member.display_name)
        message_text = message_text.replace('{server}', member.guild.name)
        message_text = message_text.replace('{memberCount}', str(member.guild.member_count))
        message_text = message_text.replace('{mention}', member.mention)

        if message_type == 'embed':
            embed = discord.Embed(title=message_title, description=message_text,
                                  color=discord.Color.green())  # Create the embed
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
        message_title = message_title.replace('{mention}', member.mention)

        message_text = message_text.replace('{user}', member.display_name)
        message_text = message_text.replace('{server}', member.guild.name)
        message_text = message_text.replace('{memberCount}', str(member.guild.member_count))
        message_text = message_text.replace('{mention}', member.mention)

        if message_type == 'embed':
            embed = discord.Embed(title=message_title, description=message_text,
                                  color=discord.Color.red())  # Create the embed
            await target_channel.send(embed=embed)  # Send it in the welcoming channel
        if message_type == 'text':
            await target_channel.send(content=message_text)  # Send it as text only

    welcome_subcommands = discord.SlashCommandGroup(name="welcome", description="Change the welcoming message")

    @welcome_subcommands.command(name="list", description="List the welcoming settings")
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @analytics("welcome list")
    async def welcome_list_settings(self, ctx: discord.ApplicationContext):
        welcome_channel = get_setting(ctx.guild.id, 'welcome_channel', '0')
        welcome_type = get_setting(ctx.guild.id, 'welcome_type', 'embed')
        welcome_title = get_setting(ctx.guild.id, 'welcome_title', 'Welcome')
        welcome_text = get_setting(ctx.guild.id, 'welcome_text', 'Welcome {user} to {server}!')

        embed = discord.Embed(title=trl(ctx.user.id, ctx.guild.id, "welcome_settings_embed_title"),
                              color=discord.Color.blurple())
        embed.add_field(name=trl(ctx.user.id, ctx.guild.id, "logging_channel"), value=welcome_channel)
        embed.add_field(name=trl(ctx.user.id, ctx.guild.id, "welcome_settings_type"), value=welcome_type)
        embed.add_field(name=trl(ctx.user.id, ctx.guild.id, "welcome_settings_title"), value=welcome_title)
        embed.add_field(name=trl(ctx.user.id, ctx.guild.id, "welcome_settings_text"), value=welcome_text)

        await ctx.respond(embed=embed, ephemeral=True)

    @welcome_subcommands.command(name='channel', description="Set the welcoming channel")
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @commands_ext.bot_has_permissions(view_channel=True, send_messages=True)
    @analytics("welcome channel")
    async def welcome_channel(self, ctx: discord.ApplicationContext, channel: discord.TextChannel):
        # Get old channel
        old_welcome_channel_id = get_setting(ctx.guild.id, "welcome_channel", '0')
        old_welcome_channel = ctx.guild.get_channel(int(old_welcome_channel_id))

        # Set new channel
        set_setting(ctx.guild.id, 'welcome_channel', str(channel.id))

        # Logging embed
        logging_embed = discord.Embed(title=trl(ctx.user.id, ctx.guild.id, "welcome_channel_log_title"))
        logging_embed.add_field(name=trl(ctx.user.id, ctx.guild.id, "logging_user"), value=f"{ctx.user.mention}")
        if old_welcome_channel is None:
            logging_embed.add_field(name=trl(ctx.user.id, ctx.guild.id, "logging_channel"), value=f"{channel.mention}")
        else:
            logging_embed.add_field(name=trl(ctx.user.id, ctx.guild.id, "logging_channel"),
                                    value=f"{old_welcome_channel.mention} -> {channel.mention}")

        # Send log
        await log_into_logs(ctx.guild, logging_embed)

        # Respond
        await ctx.respond(trl(ctx.user.id, ctx.guild.id, "welcome_channel_set", append_tip=True).format(channel=channel.mention),
                          ephemeral=True)

    @welcome_subcommands.command(name='type', description="Set whether you want to use message content or embed")
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @discord.option(name="message_type", description="The type of the message (embed or text)",
                    choices=['embed', 'text'])
    @analytics("welcome type")
    async def welcome_type(self, ctx: discord.ApplicationContext, message_type: str):
        # Get old response type
        old_welcome_type = get_setting(ctx.guild.id, "welcome_type", '0')

        # Set new response type
        set_setting(ctx.guild.id, 'welcome_type', message_type)

        # Logging embed
        logging_embed = discord.Embed(title=trl(0, ctx.guild.id, "welcome_type_log_title"))
        logging_embed.add_field(name=trl(0, ctx.guild.id, "logging_user"), value=f"{ctx.user.mention}")
        logging_embed.add_field(name=trl(0, ctx.guild.id, "logging_response_type"),
                                value=f"{old_welcome_type} -> {message_type}")

        # Send log
        await log_into_logs(ctx.guild, logging_embed)

        # Respond
        await ctx.respond(trl(ctx.user.id, ctx.guild.id, "welcome_type_set", append_tip=True).format(type=message_type), ephemeral=True)

    @welcome_subcommands.command(name='title', description="Set the title of the welcoming message")
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @discord.option(name="title", description="The title of the message")
    @analytics("welcome title")
    async def welcome_title(self, ctx: discord.ApplicationContext, title: str):
        # Get old response title
        old_welcome_title = get_setting(ctx.guild.id, "welcome_title", '0')

        # Set new message
        set_setting(ctx.guild.id, 'welcome_title', title)

        # Logging embed
        logging_embed = discord.Embed(title=trl(0, ctx.guild.id, "welcome_title_log_title"))
        logging_embed.add_field(name=trl(0, ctx.guild.id, "logging_user"), value=f"{ctx.user.mention}")
        logging_embed.add_field(name=trl(0, ctx.guild.id, "title"), value=f"{old_welcome_title} -> {title}")

        # Send log
        await log_into_logs(ctx.guild, logging_embed)

        # Respond
        await ctx.respond(trl(ctx.user.id, ctx.guild.id, "welcome_title_set", append_tip=True).format(title=title), ephemeral=True)

    @welcome_subcommands.command(name='text', description="Set the text of the welcoming message")
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @discord.option(name="text", description="The content of the message or description of the embed")
    @analytics("welcome text")
    async def welcome_text(self, ctx: discord.ApplicationContext, text: str):
        # Get old welcome text
        old_welcome_text = get_setting(ctx.guild.id, "welcome_text", '0')

        # Set new welcome text
        set_setting(ctx.guild.id, 'welcome_text', text)

        # Logging embed
        logging_embed = discord.Embed(title=trl(0, ctx.guild.id, "welcome_text_log_title"))
        logging_embed.add_field(name=trl(0, ctx.guild.id, "logging_user"), value=f"{ctx.user.mention}")
        logging_embed.add_field(name=trl(0, ctx.guild.id, "logging_text"), value=f"{old_welcome_text} -> {text}")

        # Send log
        await log_into_logs(ctx.guild, logging_embed)

        # Respond
        await ctx.respond(trl(ctx.user.id, ctx.guild.id, "welcome_text_sent", append_tip=True).format(text=text), ephemeral=True)

    goodbye_subcommands = discord.SlashCommandGroup(name="goodbye", description="Change the goodbye message")

    @goodbye_subcommands.command(name="list", description="List the goodbye settings")
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @analytics("goodbye list")
    async def goodbye_list_settings(self, ctx: discord.ApplicationContext):
        goodbye_channel = get_setting(ctx.guild.id, 'goodbye_channel', '0')
        goodbye_type = get_setting(ctx.guild.id, 'goodbye_type', 'embed')
        goodbye_title = get_setting(ctx.guild.id, 'goodbye_title', 'Welcome')
        goodbye_text = get_setting(ctx.guild.id, 'goodbye_text', 'Welcome {user} to {server}!')

        embed = discord.Embed(title=trl(ctx.user.id, ctx.guild.id, "goodbye_settings_embed_title"),
                              color=discord.Color.blurple())
        embed.add_field(name=trl(ctx.user.id, ctx.guild.id, "logging_channel"), value=goodbye_channel)
        embed.add_field(name=trl(ctx.user.id, ctx.guild.id, "goodbye_settings_type"), value=goodbye_type)
        embed.add_field(name=trl(ctx.user.id, ctx.guild.id, "goodbye_settings_title"), value=goodbye_title)
        embed.add_field(name=trl(ctx.user.id, ctx.guild.id, "goodbye_settings_text"), value=goodbye_text)

        await ctx.respond(embed=embed, ephemeral=True)

    @goodbye_subcommands.command(name='channel', description="Set the goodbye channel")
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @commands_ext.bot_has_permissions(view_channel=True, send_messages=True)
    @analytics("goodbye channel")
    async def goodbye_channel(self, ctx: discord.ApplicationContext, channel: discord.TextChannel):
        # Get old goodbye channel
        old_goodbye_channel = get_setting(ctx.guild.id, "goodbye_channel", '0')

        # Set new goodbye channel
        set_setting(ctx.guild.id, 'goodbye_channel', str(channel.id))

        # Logging embed
        logging_embed = discord.Embed(title=trl(0, ctx.guild.id, "goodbye_channel_log_title"))
        logging_embed.add_field(name=trl(0, ctx.guild.id, "logging_user"), value=f"{ctx.user.mention}")
        logging_embed.add_field(name=trl(0, ctx.guild.id, "logging_channel"),
                                value=f"{old_goodbye_channel} -> {channel.mention}")

        # Send log
        await log_into_logs(ctx.guild, logging_embed)

        # Respond
        await ctx.respond(trl(ctx.user.id, ctx.guild.id, "goodbye_channel_set", append_tip=True).format(channel=channel.mention),
                          ephemeral=True)

    @goodbye_subcommands.command(name='type', description="Set whether you want to use message content or embed")
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @discord.option(name="message_type", description="The type of the message (embed or text)",
                    choices=['embed', 'text'])
    @analytics("goodbye type")
    async def goodbye_type(self, ctx: discord.ApplicationContext, message_type: str):
        # Get old goodbye type
        old_goodbye_type = get_setting(ctx.guild.id, "goodbye_type", 'embed')

        # Set new goodbye type
        set_setting(ctx.guild.id, 'goodbye_type', message_type)

        # Logging embed
        logging_embed = discord.Embed(title=trl(0, ctx.guild.id, "goodbye_type_log_title"))
        logging_embed.add_field(name=trl(0, ctx.guild.id, "logging_user"), value=f"{ctx.user.mention}")
        logging_embed.add_field(name=trl(0, ctx.guild.id, "logging_response_type"),
                                value=f"{old_goodbye_type} -> {message_type}")

        # Send log
        await log_into_logs(ctx.guild, logging_embed)

        # Respond
        await ctx.respond(trl(ctx.user.id, ctx.guild.id, "goodbye_type_set", append_tip=True).format(type=message_type), ephemeral=True)

    @goodbye_subcommands.command(name='title', description="Set the title of the goodbye message")
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @discord.option(name="title", description="The title of the message")
    @analytics("goodbye title")
    async def goodbye_title(self, ctx: discord.ApplicationContext, title: str):
        # Get old goodbye title
        old_goodbye_title = get_setting(ctx.guild.id, "goodbye_title", 'Welcome')

        # Set new goodbye title
        set_setting(ctx.guild.id, 'goodbye_title', title)

        # Logging embed
        logging_embed = discord.Embed(title=trl(0, ctx.guild.id, "goodbye_title_log_title"))
        logging_embed.add_field(name=trl(0, ctx.guild.id, "logging_user"), value=f"{ctx.user.mention}")
        logging_embed.add_field(name=trl(0, ctx.guild.id, "title"), value=f"{old_goodbye_title} -> {title}")

        # Send log
        await log_into_logs(ctx.guild, logging_embed)

        # Respond
        await ctx.respond(trl(ctx.user.id, ctx.guild.id, "goodbye_title_set", append_tip=True).format(title=title), ephemeral=True)

    @goodbye_subcommands.command(name='text', description="Set the text of the goodbye message")
    @discord.default_permissions(manage_guild=True)
    @commands_ext.has_permissions(manage_guild=True)
    @commands_ext.guild_only()
    @discord.option(name="text", description="The content of the message or description of the embed")
    @analytics("goodbye text")
    async def goodbye_text(self, ctx: discord.ApplicationContext, text: str):
        # Get old goodbye text
        old_goodbye_text = get_setting(ctx.guild.id, "goodbye_text", 'Welcome {user} to {server}!')

        # Set new goodbye text
        set_setting(ctx.guild.id, 'goodbye_text', text)

        # Logging embed
        logging_embed = discord.Embed(title=trl(0, ctx.guild.id, "goodbye_text_log_title"))
        logging_embed.add_field(name=trl(0, ctx.guild.id, "logging_user"), value=f"{ctx.user.mention}")
        logging_embed.add_field(name=trl(0, ctx.guild.id, "logging_text"), value=f"{old_goodbye_text} -> {text}")

        # Send log
        await log_into_logs(ctx.guild, logging_embed)

        # Respond
        await ctx.respond(trl(ctx.user.id, ctx.guild.id, "goodbye_text_set", append_tip=True).format(text=text), ephemeral=True)
