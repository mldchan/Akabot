import discord
from discord.ext import commands as discord_commands_ext
from discord.ext import pages as dc_pages

from database import get_conn
from utils.languages import get_translation_for_key_localized as trl


class AutoResponse(discord.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        super().__init__()
        self.bot = bot

        async def init_async():
            db = await get_conn()

            # Create table
            await db.execute(
                "CREATE TABLE IF NOT EXISTS auto_response(id integer primary key autoincrement, guild_id integer, trigger_text text, reply_text text)")

            # Save changes
            await db.commit()
            await db.close()

        self.bot.loop.create_task(init_async())

    auto_response_group = discord.SlashCommandGroup(name="auto_response", description="Auto response settings")

    @auto_response_group.command(name="add", description="New auto response setting")
    @discord.option(name="trigger", description="The trigger of the message. Can be any text. Case insensitive.")
    @discord.option(name="reply", description="What to reply with. This exact text will be sent")
    @discord_commands_ext.has_permissions(manage_messages=True)
    @discord_commands_ext.bot_has_permissions(read_message_history=True, add_reactions=True)
    @discord.default_permissions(manage_messages=True)
    async def add_auto_response(self, ctx: discord.ApplicationContext, trigger: str, reply: str):
        db = await get_conn()

        # Insert
        await db.execute("INSERT INTO auto_response(guild_id, trigger_text, reply_text) VALUES (?, ?, ?)",
                    (ctx.guild.id, trigger, reply))

        # Save
        await db.commit()
        await db.close()

        # Respond
        await ctx.respond(
            (await trl(ctx.user.id, ctx.guild.id, "auto_response_add_success")).format(trigger=trigger, reply=reply),
            ephemeral=True)

    @auto_response_group.command(name="list", description="List auto response settings")
    @discord_commands_ext.has_permissions(manage_messages=True)
    @discord_commands_ext.bot_has_permissions(read_message_history=True, add_reactions=True)
    @discord.default_permissions(manage_messages=True)
    async def list_auto_responses(self, ctx: discord.ApplicationContext):
        db = await get_conn()

        # Define a message variable
        message_groups = []
        current_group = 0
        current_group_msg = ""

        # List
        cur = await db.execute("SELECT * FROM auto_response WHERE guild_id=?", (ctx.guild.id,))

        all_settings = await cur.fetchall()
        await db.close()
        if len(all_settings) == 0:
            await ctx.respond(trl(ctx.user.id, ctx.guild.id, "auto_response_list_empty"), ephemeral=True)
            return

        for i in all_settings:
            # Format: **{id}**: {trigger} -> {reply}
            # current_group_msg += f"**ID: `{i[0]}`**: Trigger: `{i[2]}` -> Will say `{i[3]}`\n"
            current_group_msg += (await trl(ctx.user.id, ctx.guild.id, "auto_response_list_row")).format(id=i[0], trigger=i[2],
                                                                                                 reply=i[3])
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

    @auto_response_group.command(name="edit_trigger", description="Change trigger for a setting")
    @discord_commands_ext.has_permissions(manage_messages=True)
    @discord_commands_ext.bot_has_permissions(read_message_history=True, add_reactions=True)
    @discord.default_permissions(manage_messages=True)
    async def edit_trigger_auto_response(self, ctx: discord.ApplicationContext, edit_response_id: int, new_trigger: str):
        db = await get_conn()
        # Check if ID exists
        cur = await db.execute("SELECT * FROM auto_response WHERE guild_id=? AND id=?", (ctx.guild.id, edit_response_id))
        if await cur.fetchone() is None:
            await ctx.respond(
                trl(ctx.user.id, ctx.guild.id, "auto_response_setting_not_found"),
                ephemeral=True)
            return

        # Update
        await db.execute("UPDATE auto_response SET trigger_text=? WHERE id=?", (new_trigger, edit_response_id))

        # Save
        await db.commit()
        await db.close()

        # Respond
        await ctx.respond(trl(ctx.user.id, ctx.guild.id, "auto_response_keyword_updated"), ephemeral=True)

    @auto_response_group.command(name="delete", description="Delete an auto response setting")
    @discord_commands_ext.has_permissions(manage_messages=True)
    @discord_commands_ext.bot_has_permissions(read_message_history=True, add_reactions=True)
    @discord.default_permissions(manage_messages=True)
    async def delete_auto_response(self, ctx: discord.ApplicationContext, delete_response_id: int):
        db = await get_conn()
        # Check if ID exists
        cur = await db.execute("SELECT * FROM auto_response WHERE guild_id=? AND id=?", (ctx.guild.id, delete_response_id))
        if await cur.fetchone() is None:
            await ctx.respond(
                trl(ctx.user.id, ctx.guild.id, "auto_response_setting_not_found"),
                ephemeral=True)
            return

        # Delete
        await db.execute("DELETE FROM auto_response WHERE id=?", (delete_response_id,))

        # Save
        await db.commit()
        await db.close()

        # Respond
        await ctx.respond(trl(ctx.user.id, ctx.guild.id, "auto_response_delete_success"), ephemeral=True)

    @auto_response_group.command(name="edit_response", description="Change response for a setting")
    @discord_commands_ext.has_permissions(manage_messages=True)
    @discord_commands_ext.bot_has_permissions(read_message_history=True, add_reactions=True)
    @discord.default_permissions(manage_messages=True)
    async def edit_response_auto_response(self, ctx: discord.ApplicationContext, edit_response_id: int, new_response: str):
        db = await get_conn()
        # Check if ID exists
        cur = await db.execute("SELECT * FROM auto_response WHERE guild_id=? AND id=?", (ctx.guild.id, edit_response_id))
        if await cur.fetchone() is None:
            await ctx.respond(
                trl(ctx.user.id, ctx.guild.id, "auto_response_setting_not_found"),
                ephemeral=True)
            return

        # Update
        await db.execute("UPDATE auto_response SET reply_text=? WHERE id=?", (new_response, edit_response_id))

        # Save
        await db.commit()
        await db.close()

        # Respond
        await ctx.respond(trl(ctx.user.id, ctx.guild.id, "auto_response_text_updated"), ephemeral=True)

    @discord.Cog.listener()
    async def on_message(self, msg: discord.Message):

        db = await get_conn()

        # Check if it's the bot
        if msg.author.bot:
            return

        # Find all created settings
        cur = await db.execute("SELECT * FROM auto_response WHERE guild_id=?", (msg.guild.id,))
        fetch_all = await cur.fetchall()
        await db.close()
        for i in fetch_all:
            # If it contains the message
            if i[2] in msg.content:
                # Reply to it
                await msg.reply(i[3])
