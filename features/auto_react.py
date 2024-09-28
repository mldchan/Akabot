import discord
import emoji as emoji_package
from discord.ext import commands as discord_commands_ext
from discord.ext import pages as dc_pages

from database import get_conn
from utils.languages import get_translation_for_key_localized as trl


class AutoReact(discord.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot
        super().__init__()

        async def init_async():
            db = await get_conn()

            # Create table
            await db.execute(
                "CREATE TABLE IF NOT EXISTS auto_react(id integer primary key autoincrement, guild_id integer, trigger_text text, emoji text)")

            # Save changes
            await db.commit()
            await db.close()

        self.bot.loop.create_task(init_async())

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

        db = await get_conn()

        # Insert
        await db.execute("INSERT INTO auto_react(guild_id, trigger_text, emoji) VALUES (?, ?, ?)",
                    (ctx.guild.id, trigger, str(emoji)))

        # Save
        await db.commit()
        await db.close()

        # Respond
        await ctx.respond(
            (await trl(ctx.user.id, ctx.guild.id, "auto_react_add_success")).format(trigger=trigger, emoji=str(emoji)),
            ephemeral=True)

    @auto_react_group.command(name="list", description="List auto react settings")
    @discord_commands_ext.has_permissions(manage_messages=True)
    @discord_commands_ext.bot_has_permissions(read_message_history=True, add_reactions=True)
    @discord.default_permissions(manage_messages=True)
    async def list_auto_reacts(self, ctx: discord.ApplicationContext):
        db = await get_conn()

        # Define a message variable
        message_groups = []
        current_group = 0
        current_group_msg = ""

        # List
        cur = await db.execute("SELECT * FROM auto_react WHERE guild_id = ?", (ctx.guild.id,))
        all_settings = await cur.fetchall()
        await db.close()
        if len(all_settings) == 0:
            await ctx.respond(trl(ctx.user.id, ctx.guild.id, "auto_react_list_empty"), ephemeral=True)
            return

        for i in all_settings:
            # Format: **{id}**: {trigger} -> {reply}

            # current_group_msg += f"**ID: `{i[0]}`**: Trigger: `{i[2]}` -> Will react with `{i[3]}`\n"
            current_group_msg += (await trl(ctx.user.id, ctx.guild.id, "auto_react_list_row")).format(id=i[0], trigger=i[2],
                                                                                              emoji=i[3])
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
    async def edit_trigger_auto_react(self, ctx: discord.ApplicationContext, edit_react_id: int, new_trigger: str):
        db = await get_conn()
        # Check if ID exists
        cur = await db.execute("SELECT * FROM auto_react WHERE guild_id=? AND id=?", (ctx.guild.id, edit_react_id))
        if await cur.fetchone() is None:
            await ctx.respond(trl(ctx.user.id, ctx.guild.id, "auto_react_setting_not_found"),
                              ephemeral=True)
            return

        # Update
        await db.execute("UPDATE auto_react SET trigger_text=? WHERE id=?", (new_trigger, edit_react_id))

        # Save
        await db.commit()
        await db.close()

        # Respond
        await ctx.respond(trl(ctx.user.id, ctx.guild.id, "auto_react_keyword_updated_success"), ephemeral=True)

    @auto_react_group.command(name="delete", description="Delete an auto react setting")
    @discord_commands_ext.has_permissions(manage_messages=True)
    @discord_commands_ext.bot_has_permissions(read_message_history=True, add_reactions=True)
    @discord.default_permissions(manage_messages=True)
    async def delete_auto_react(self, ctx: discord.ApplicationContext, delete_react_id: int):
        db = await get_conn()
        # Check if ID exists
        cur = await db.execute("SELECT * FROM auto_react WHERE guild_id=? AND id=?", (ctx.guild.id, delete_react_id))
        if await cur.fetchone() is None:
            await ctx.respond(
                trl(ctx.user.id, ctx.guild.id, "auto_react_setting_not_found"),
                ephemeral=True)
            return

        # Delete
        await db.execute("DELETE FROM auto_react WHERE id=?", (delete_react_id,))

        # Save
        await db.commit()
        await db.close()

        # Respond
        await ctx.respond(trl(ctx.user.id, ctx.guild.id, "auto_react_delete_success"), ephemeral=True)

    @auto_react_group.command(name="edit_react_emoji", description="Change react for a setting")
    @discord_commands_ext.has_permissions(manage_messages=True)
    @discord_commands_ext.bot_has_permissions(read_message_history=True, add_reactions=True)
    @discord.default_permissions(manage_messages=True)
    async def edit_response_auto_react(self, ctx: discord.ApplicationContext, edit_react_id: int, new_emoji: str):
        # Parse le emoji
        emoji = discord.PartialEmoji.from_str(new_emoji.strip())
        if emoji.is_custom_emoji():
            # Check if the emoji is from the current server
            if emoji.id is None:
                await ctx.respond(trl(ctx.user.id, ctx.guild.id, "auto_react_emoji_invalid"), ephemeral=True)
                return

            emoji_s = await ctx.guild.fetch_emoji(emoji.id)
            if emoji_s is None:
                await ctx.respond(trl(ctx.user.id, ctx.guild.id, "auto_react_emoji_invalid"), ephemeral=True)
                return
        else:
            if not emoji_package.is_emoji(new_emoji.strip()):
                await ctx.respond(trl(ctx.user.id, ctx.guild.id, "auto_react_emoji_invalid"), ephemeral=True)
                return

        db = await get_conn()
        # Check if ID exists
        cur = await db.execute("SELECT * FROM auto_react WHERE guild_id=? AND id=?", (ctx.guild.id, edit_react_id))
        if await cur.fetchone() is None:
            await ctx.respond(
                trl(ctx.user.id, ctx.guild.id, "auto_react_setting_not_found"),
                ephemeral=True)
            return

        # Update
        await db.execute("UPDATE auto_react SET emoji=? WHERE id=?", (str(emoji), edit_react_id))

        # Save
        await db.commit()
        await db.close()

        # Respond
        await ctx.respond(trl(ctx.user.id, ctx.guild.id, "auto_react_emoji_set_success"), ephemeral=True)

    @discord.Cog.listener()
    async def on_message(self, msg: discord.Message):

        db = await get_conn()

        # Check if it's the bot
        if msg.author.bot:
            return

        # Find all created settings
        cur = await db.execute("SELECT * FROM auto_react WHERE guild_id=?", (msg.guild.id,))
        fetch_all = await cur.fetchall()
        await db.close()
        for i in fetch_all:
            # If it contains the message
            if i[2] in msg.content:
                # Parse the emoji
                emoji = discord.PartialEmoji.from_str(i[3])
                # Add le reaction to it
                await msg.add_reaction(emoji)
