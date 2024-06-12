
import discord
from database import conn
from discord.ext import pages as dc_pages

class AutoResponse(discord.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        super().__init__()
        self.bot = bot

        cur = conn.cursor()
        
        # Create table
        cur.execute("CREATE TABLE IF NOT EXISTS auto_response(id integer primary key autoincrement, channel_id integer, trigger_text text, reply_text text)")

        # Save changes
        cur.close()
        conn.commit()


    auto_response_group = discord.SlashCommandGroup(name="auto_response", description="Auto response settings")

    @auto_response_group.command(name="add", description="New auto response setting")
    @discord.option(name="trigger", description="The trigger of the message. Can be any text. Case insensitive.")
    @discord.option(name="reply", description="What to reply with. This exact text will be sent")
    async def add_auto_response(self, ctx: discord.ApplicationContext, trigger: str, reply: str):
        cur = conn.cursor()

        # Insert
        cur.execute("INSERT INTO auto_response(channel_id, trigger_text, reply_text) VALUES (?, ?, ?)",
                    (ctx.channel.id, trigger, reply))        
        
        # Save
        cur.close()
        conn.commit()

        # Respond
        await ctx.respond(f"Added trigger `{trigger}` that will make the bot reply with `{reply}`", ephemeral=True)

    @auto_response_group.command(name="list", description="List auto response settings")
    async def list_auto_responses(self, ctx: discord.ApplicationContext):
        cur = conn.cursor()
        
        # Define a message variable
        message_groups = []
        current_group = 0
        current_group_msg = ""

        # List
        cur.execute("SELECT * FROM auto_response WHERE channel_id=?", (ctx.channel.id,))

        all_settings = cur.fetchall()
        if all_settings is None:
            await ctx.respond("There are no settings set on this Discord server.", ephemeral=True)
            return

        for i in all_settings:
            # Format: **{id}**: {trigger} -> {reply}
            current_group_msg += f"**ID: `{i[0]}`**: Trigger: `{i[2]}` -> Will say `{i[3]}`\n"
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
    async def edit_trigger_auto_response(self, ctx: discord.ApplicationContext, id: int, new_trigger: str):
        cur = conn.cursor()
        # Check if ID exists
        cur.execute("SELECT * FROM auto_response WHERE channel_id=? AND id=?", (ctx.channel.id, id))
        if cur.fetchone() is None:
            await ctx.respond("The setting was not found. You'll need to run this in the channel where the setting was set.", ephemeral=True)
            return
        
        # Update
        cur.execute("UPDATE auto_response SET trigger=? WHERE id=?", (new_trigger, id))

        # Save
        cur.close()
        conn.commit()

        # Respond
        await ctx.respond("The trigger keyword was updated successfully.", ephemeral=True)

    @auto_response_group.command(name="delete", description="Delete an auto response setting")
    async def delete_auto_response(self, ctx: discord.ApplicationContext, id: int):
        cur = conn.cursor()
        # Check if ID exists
        cur.execute("SELECT * FROM auto_response WHERE channel_id=? AND id=?", (ctx.channel.id, id))
        if cur.fetchone() is None:
            await ctx.respond("The setting was not found. You'll need to run this in the channel where the setting was set.", ephemeral=True)
            return
        
        # Delete
        cur.execute("DELETE FROM auto_response WHERE id=?", (id,))

        # Save
        cur.close()
        conn.commit()

        # Respond
        await ctx.respond("Deleted the setting successfully.", ephemeral=True)


    @auto_response_group.command(name="edit_response", description="Change response for a setting")
    async def edit_response_auto_response(self, ctx: discord.ApplicationContext, id: int, new_response: str):
        cur = conn.cursor()
        # Check if ID exists
        cur.execute("SELECT * FROM auto_response WHERE channel_id=? AND id=?", (ctx.channel.id, id))
        if cur.fetchone() is None:
            await ctx.respond("The setting was not found. You'll need to run this in the channel where the setting was set.", ephemeral=True)
            return
        
        # Update
        cur.execute("UPDATE auto_response SET reply_text=? WHERE id=?", (new_response, id))

        # Save
        cur.close()
        conn.commit()

        # Respond
        await ctx.respond("The response text was updated successfully.", ephemeral=True)


    @discord.Cog.listener()
    async def on_message(self, msg: discord.Message):
        
        cur = conn.cursor()

        # Check if it's the bot
        if msg.author.bot:
            return

        # Find all created settings
        cur.execute("SELECT * FROM auto_response WHERE channel_id=?", (msg.channel.id,))
        for i in cur.fetchall():
            # If it contains the message
            if i[2] in msg.content:
                # Reply to it
                await msg.reply(i[3])

