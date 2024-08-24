import discord

from database import conn
from utils.analytics import analytics
from utils.languages import get_translation_for_key_localized as trl


class RolesOnJoin(discord.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS roles_on_join(id integer primary key autoincrement, guild_id integer, role_id integer)")
        cur.close()
        conn.commit()

    @discord.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        cur = conn.cursor()
        cur.execute("SELECT role_id FROM roles_on_join WHERE guild_id=?", (member.guild.id,))
        rows = cur.fetchall()
        for row in rows:
            role = member.guild.get_role(row[0])
            # check role position
            if role.position > member.guild.me.top_role.position:
                continue
            if role is not None:
                await member.add_roles(role)
            else:
                # remove
                cur.execute("DELETE FROM roles_on_join WHERE id=?", (row[0],))
                conn.commit()

    roles_on_join_commands = discord.SlashCommandGroup(name="roles_on_join", description="Add roles on join")

    @roles_on_join_commands.command(name="add", description="Add a role on join")
    @analytics("roles_on_join add")
    async def add_role_on_join(self, ctx: discord.ApplicationContext, role: discord.Role):
        # check role position
        if role.position > ctx.me.top_role.position:
            await ctx.respond(trl(ctx.user.id, ctx.guild.id, "roles_on_join_role_above_bot"), ephemeral=True)
            return

        cur = conn.cursor()

        cur.execute("SELECT role_id FROM roles_on_join WHERE guild_id=? AND role_id=?", (ctx.guild_id, role.id))
        if cur.fetchone():
            await ctx.respond(trl(ctx.user.id, ctx.guild.id, "roles_on_join_role_already_in_join_roles"),
                              ephemeral=True)
            return

        cur.execute("INSERT INTO roles_on_join(guild_id, role_id) VALUES (?, ?)", (ctx.guild_id, role.id))
        conn.commit()
        await ctx.respond(trl(ctx.user.id, ctx.guild.id, "roles_on_join_role_added", append_tip=True), ephemeral=True)

    @roles_on_join_commands.command(name="remove", description="Remove a role on join")
    @analytics("roles_on_join remove")
    async def remove_role_on_join(self, ctx: discord.ApplicationContext, role: discord.Role):
        cur = conn.cursor()
        cur.execute("SELECT role_id FROM roles_on_join WHERE guild_id=? AND role_id=?", (ctx.guild_id, role.id))
        if not cur.fetchone():
            await ctx.respond(trl(ctx.user.id, ctx.guild.id, "roles_on_join_role_not_in_join_roles"), ephemeral=True)
            return

        cur.execute("DELETE FROM roles_on_join WHERE guild_id=? AND role_id=?", (ctx.guild_id, role.id))
        conn.commit()
        await ctx.respond(trl(ctx.user.id, ctx.guild.id, "roles_on_join_role_removed", append_tip=True), ephemeral=True)

    @roles_on_join_commands.command(name="list", description="List roles on join")
    @analytics("roles_on_join list")
    async def list_roles_on_join(self, ctx: discord.ApplicationContext):
        cur = conn.cursor()
        cur.execute("SELECT id, role_id FROM roles_on_join WHERE guild_id=?", (ctx.guild_id,))
        rows = cur.fetchall()
        if not rows:
            await ctx.respond(trl(ctx.user.id, ctx.guild.id, "roles_on_join_list_no_roles_on_join", append_tip=True), ephemeral=True)
            return

        msg = ""
        # format - {mention}
        for row in rows:
            role = ctx.guild.get_role(row[1])
            if role is None:
                cur.execute("DELETE FROM roles_on_join WHERE id=?", (row[0],))
                conn.commit()
                continue
            msg = f"{msg}\n{role.mention}"

        embed = discord.Embed(title="Roles on join", description=msg, color=discord.Color.blurple())
        await ctx.respond(embed=embed, ephemeral=True)
