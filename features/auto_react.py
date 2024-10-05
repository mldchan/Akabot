import discord
import emoji as emoji_package
from bson import ObjectId
from discord.ext import commands as discord_commands_ext
from discord.ext import pages as dc_pages

from database import client
from utils.languages import get_translation_for_key_localized as trl


class AutoReact(discord.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot
        super().__init__()

    auto_react_group = discord.SlashCommandGroup(name="auto_react", description="Auto react settings")

    @auto_react_group.command(name="add", description="New auto react setting")
    @discord.option(name="trigger", description="The trigger of the message. Can be any text. Case insensitive.")
    @discord.option(name="emoji", description="What emoji to react with. You MUST paste an emoji.")
    @discord_commands_ext.has_permissions(manage_messages=True)
    @discord_commands_ext.bot_has_permissions(read_message_history=True, add_reactions=True)
    @discord.default_permissions(manage_messages=True)
    async def add_auto_react(self, ctx: discord.ApplicationContext, trigger: str, emoji_input: str):
        # Parse le emoji
        emoji = discord.PartialEmoji.from_str(emoji_input.strip())

        if emoji.is_custom_emoji():
            # Custom emoji check
            if emoji.id is None:
                await ctx.respond(trl(ctx.user.id, ctx.guild.id, "auto_react_emoji_invalid"), ephemeral=True)
                return

            emoji_s = await ctx.guild.fetch_emoji(emoji.id)
            if emoji_s is None:
                await ctx.respond(trl(ctx.user.id, ctx.guild.id, "auto_react_emoji_invalid"), ephemeral=True)
                return
        else:
            # Regex check
            if not emoji_package.is_emoji(emoji_input):
                await ctx.respond(trl(ctx.user.id, ctx.guild.id, "auto_react_emoji_invalid"), ephemeral=True)
                return

        client['AutoReact'].insert_one({'GuildID': str(ctx.guild.id), 'TriggerText': trigger, 'Emoji': str(emoji)})

        # Respond
        await ctx.respond(
            trl(ctx.user.id, ctx.guild.id, "auto_react_add_success").format(trigger=trigger, emoji=str(emoji)),
            ephemeral=True)

    @auto_react_group.command(name="list", description="List auto react settings")
    @discord_commands_ext.has_permissions(manage_messages=True)
    @discord_commands_ext.bot_has_permissions(read_message_history=True, add_reactions=True)
    @discord.default_permissions(manage_messages=True)
    async def list_auto_reacts(self, ctx: discord.ApplicationContext):
        # Define a message variable
        message_groups = []
        current_group = 0
        current_group_msg = ""

        # List
        all_settings = client['AutoReact'].find({'GuildID': {'$eq': str(ctx.guild.id)}}).to_list()
        if len(all_settings) == 0:
            await ctx.respond(trl(ctx.user.id, ctx.guild.id, "auto_react_list_empty"), ephemeral=True)
            return

        for i in all_settings:
            # Format: **{id}**: {trigger} -> {reply}

            # current_group_msg += f"**ID: `{i[0]}`**: Trigger: `{i[2]}` -> Will react with `{i[3]}`\n"
            current_group_msg += trl(ctx.user.id, ctx.guild.id, "auto_react_list_row").format(id=str(i['_id']), trigger=i['TriggerText'],
                                                                                              emoji=i['Emoji'])
            current_group += 1

            # Split message group
            if current_group == 5:
                message_groups.append(current_group)
                current_group = 0
                current_group_msg = ""

        # Add last group
        if current_group != 0:
            message_groups.append(current_group_msg)

        # Reply with a paginator
        paginator = dc_pages.Paginator(message_groups)
        await paginator.respond(ctx.interaction, ephemeral=True)

    @auto_react_group.command(name="edit_trigger", description="Change trigger for a setting")
    @discord_commands_ext.has_permissions(manage_messages=True)
    @discord_commands_ext.bot_has_permissions(read_message_history=True, add_reactions=True)
    @discord.default_permissions(manage_messages=True)
    async def edit_trigger_auto_react(self, ctx: discord.ApplicationContext, id: str, new_trigger: str):
        if not ObjectId.is_valid(id):
            await ctx.respond(trl(ctx.user.id, ctx.guild.id, "auto_react_setting_not_found"),
                              ephemeral=True)
            return

        edited = client['AutoReact'].update_one({'_id': ObjectId(id), 'GuildID': str(ctx.guild.id)}, {'$set': {'TriggerText': new_trigger}})

        if edited.matched_count == 0:
            await ctx.respond(trl(ctx.user.id, ctx.guild.id, "auto_react_setting_not_found"),
                              ephemeral=True)
            return

        await ctx.respond(trl(ctx.user.id, ctx.guild.id, "auto_react_keyword_updated_success"), ephemeral=True)

    @auto_react_group.command(name="delete", description="Delete an auto react setting")
    @discord_commands_ext.has_permissions(manage_messages=True)
    @discord_commands_ext.bot_has_permissions(read_message_history=True, add_reactions=True)
    @discord.default_permissions(manage_messages=True)
    async def delete_auto_react(self, ctx: discord.ApplicationContext, id: int):
        delete = client['AutoReact'].delete_one({'ID': id, 'GuildID': str(ctx.guild.id)})

        if delete.deleted_count == 0:
            await ctx.respond(trl(ctx.user.id, ctx.guild.id, "auto_react_setting_not_found"),
                              ephemeral=True)
            return

        # Respond
        await ctx.respond(trl(ctx.user.id, ctx.guild.id, "auto_react_delete_success"), ephemeral=True)

    @auto_react_group.command(name="edit_react_emoji", description="Change react for a setting")
    @discord_commands_ext.has_permissions(manage_messages=True)
    @discord_commands_ext.bot_has_permissions(read_message_history=True, add_reactions=True)
    @discord.default_permissions(manage_messages=True)
    async def edit_response_auto_react(self, ctx: discord.ApplicationContext, id: str, new_emoji: str):
        # Parse le emoji
        emoji = discord.PartialEmoji.from_str(new_emoji.strip())
        if emoji.is_custom_emoji():
            # Check if the emoji is from the current server
            if emoji.id is None:
                await ctx.respond(trl(ctx.user.id, ctx.guild.id, "auto_react_emoji_invalid"), ephemeral=True)
                return

            for i in ctx.guild.emojis:
                if i.id == emoji.id:
                    break
            else:
                await ctx.respond(trl(ctx.user.id, ctx.guild.id, "auto_react_emoji_invalid"), ephemeral=True)
                return
        else:
            if not emoji_package.is_emoji(new_emoji.strip()):
                await ctx.respond(trl(ctx.user.id, ctx.guild.id, "auto_react_emoji_invalid"), ephemeral=True)
                return

        if not ObjectId.is_valid(id):
            await ctx.respond(trl(ctx.user.id, ctx.guild.id, "auto_react_setting_not_found"),
                              ephemeral=True)
            return

        updated = client['AutoReact'].update_one({'_id': ObjectId(id), 'GuildID': str(ctx.guild.id)},
                                                 {'$set': {'Emoji': str(emoji)}})

        if updated.matched_count == 0:
            await ctx.respond(trl(ctx.user.id, ctx.guild.id, "auto_react_setting_not_found"),
                ephemeral=True)
            return

        # Respond
        await ctx.respond(trl(ctx.user.id, ctx.guild.id, "auto_react_emoji_set_success"), ephemeral=True)

    @discord.Cog.listener()
    async def on_message(self, msg: discord.Message):
        # Check if it's the bot
        if msg.author.bot:
            return

        # Find all created settings
        data = client['AutoReact'].find({'GuildID': str(msg.guild.id)}).to_list()
        for i in data:
            # If it contains the message
            if i['TriggerText'] in msg.content:
                # Parse the emoji
                emoji = discord.PartialEmoji.from_str(i['Emoji'])
                # Add le reaction to it
                await msg.add_reaction(emoji)
