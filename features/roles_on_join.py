import discord

from database import get_conn
from utils.analytics import analytics
from utils.languages import get_translation_for_key_localized as trl


class RolesOnJoin(discord.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

        async def init_async():
            db = await get_conn()
            await db.execute(
                "CREATE TABLE IF NOT EXISTS roles_on_join(id integer primary key autoincrement, guild_id integer, role_id integer)")
            await db.commit()
            await db.close()

        self.bot.loop.create_task(init_async())

    @discord.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        db = await get_conn()
        cur = await db.execute("SELECT role_id FROM roles_on_join WHERE guild_id=?", (member.guild.id,))
        rows = await cur.fetchall()
        for row in rows:
            role = member.guild.get_role(row[0])
            # check role position
            if role.position > member.guild.me.top_role.position:
                continue
            if role is not None:
                await member.add_roles(role)
            else:
                # remove
                await db.execute("DELETE FROM roles_on_join WHERE id=?", (row[0],))

        await db.commit()
        await db.close()

    roles_on_join_commands = discord.SlashCommandGroup(name="roles_on_join", description="Add roles on join")

    @roles_on_join_commands.command(name="add", description="Add a role on join")
    @analytics("roles_on_join add")
    async def add_role_on_join(self, ctx: discord.ApplicationContext, role: discord.Role):
        # check role position
        if role.position > ctx.me.top_role.position:
            await ctx.respond(await trl(ctx.user.id, ctx.guild.id, "roles_on_join_role_above_bot"), ephemeral=True)
            return

        db = await get_conn()

        cur = await db.execute("SELECT role_id FROM roles_on_join WHERE guild_id=? AND role_id=?", (ctx.guild_id, role.id))
        if await cur.fetchone():
            await ctx.respond(await trl(ctx.user.id, ctx.guild.id, "roles_on_join_role_already_in_join_roles"),
                              ephemeral=True)
            await db.close()
            return

        await db.execute("INSERT INTO roles_on_join(guild_id, role_id) VALUES (?, ?)", (ctx.guild_id, role.id))
        await db.commit()
        await db.close()
        await ctx.respond(await trl(ctx.user.id, ctx.guild.id, "roles_on_join_role_added", append_tip=True), ephemeral=True)

    @roles_on_join_commands.command(name="remove", description="Remove a role on join")
    @analytics("roles_on_join remove")
    async def remove_role_on_join(self, ctx: discord.ApplicationContext, role: discord.Role):
        db = await get_conn()
        cur = await db.execute("SELECT role_id FROM roles_on_join WHERE guild_id=? AND role_id=?", (ctx.guild_id, role.id))
        if not await cur.fetchone():
            await ctx.respond(await trl(ctx.user.id, ctx.guild.id, "roles_on_join_role_not_in_join_roles"), ephemeral=True)
            await db.close()
            return

        await db.execute("DELETE FROM roles_on_join WHERE guild_id=? AND role_id=?", (ctx.guild_id, role.id))
        await db.commit()
        await db.close()
        await ctx.respond(await trl(ctx.user.id, ctx.guild.id, "roles_on_join_role_removed", append_tip=True), ephemeral=True)

    @roles_on_join_commands.command(name="list", description="List roles on join")
    @analytics("roles_on_join list")
    async def list_roles_on_join(self, ctx: discord.ApplicationContext):
        db = await get_conn()
        cur = await db.execute("SELECT id, role_id FROM roles_on_join WHERE guild_id=?", (ctx.guild_id,))
        rows = await cur.fetchall()
        if not rows:
            await ctx.respond(await trl(ctx.user.id, ctx.guild.id, "roles_on_join_list_no_roles_on_join", append_tip=True), ephemeral=True)
            await db.close()
            return

        msg = ""
        # format - {mention}
        for row in rows:
            role = ctx.guild.get_role(row[1])
            if role is None:
                await db.execute("DELETE FROM roles_on_join WHERE id=?", (row[0],))
                continue
            msg = f"{msg}\n{role.mention}"

        embed = discord.Embed(title="Roles on join", description=msg, color=discord.Color.blurple())
        await ctx.respond(embed=embed, ephemeral=True)

        await db.commit()
        await db.close()
