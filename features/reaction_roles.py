import discord
from discord.ext import commands as commands_ext

from utils.analytics import analytics
from utils.blocked import is_blocked


def get_roles(msg: discord.Message):
    roles = []

    if msg.guild is None:
        return []

    for i in msg.components:
        if not isinstance(i, discord.ActionRow):
            continue

        for j in i.children:
            if not isinstance(j, discord.Button):
                continue

            split = j.custom_id.split('-')
            if len(split) != 2:
                continue

            if split[0] not in ['rrn', 'rra', 'rrr', 'rrs']:
                continue

            if not split[1].isdigit():
                continue

            role = msg.guild.get_role(int(split[1]))
            if role is None:
                continue

            roles.append(role)

    return roles


class ReactionRoles(discord.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        super().__init__()

        self.bot = bot

    create_reaction_role_subcommand = discord.SlashCommandGroup(name="create_reaction_role",
                                                                description="Create a reaction role")

    def create_view(self, type: str, roles: list[discord.Role]) -> discord.ui.View:
        view = discord.ui.View()
        for role in roles:
            if role is None:
                continue

            view.add_item(
                discord.ui.Button(style=discord.ButtonStyle.primary, label=role.name, custom_id=f"rr{type}-{role.id}"))

        return view

    @create_reaction_role_subcommand.command(name="normal", description="Create a normal reaction role")
    @commands_ext.has_permissions(manage_roles=True)
    @commands_ext.guild_only()
    @is_blocked()
    @analytics("create_reaction_role normal")
    async def create_reaction_role_normal(self, interaction: discord.ApplicationContext, message: str, role: discord.Role,
                                          role_2: discord.Role = None, role_3: discord.Role = None,
                                          role_4: discord.Role = None, role_5: discord.Role = None) -> None:
        view = self.create_view('n', [role, role_2, role_3, role_4, role_5])

        await interaction.channel.send(content=message, view=view)
        await interaction.response.send_message("Reaction role has been created!", ephemeral=True)

    @create_reaction_role_subcommand.command(name="add_only", description="Create an add only reaction role")
    @commands_ext.has_permissions(manage_roles=True)
    @commands_ext.guild_only()
    @is_blocked()
    @analytics("create_reaction_role add_only")
    async def create_reaction_role_add(self, interaction: discord.ApplicationContext, message: str, role: discord.Role,
                                       role_2: discord.Role = None, role_3: discord.Role = None,
                                       role_4: discord.Role = None, role_5: discord.Role = None) -> None:
        view = self.create_view('a', [role, role_2, role_3, role_4, role_5])

        await interaction.channel.send(content=message, view=view)
        await interaction.response.send_message("Reaction role has been created!", ephemeral=True)

    @create_reaction_role_subcommand.command(name="remove_only", description="Create a remove only reaction role")
    @commands_ext.has_permissions(manage_roles=True)
    @commands_ext.guild_only()
    @is_blocked()
    @analytics("create_reaction_role remove_only")
    async def create_reaction_role_remove(self, interaction: discord.ApplicationContext, message: str, role: discord.Role,
                                          role_2: discord.Role = None, role_3: discord.Role = None,
                                          role_4: discord.Role = None, role_5: discord.Role = None) -> None:
        view = self.create_view('r', [role, role_2, role_3, role_4, role_5])

        await interaction.channel.send(content=message, view=view)
        await interaction.response.send_message("Reaction role has been created!", ephemeral=True)

    @create_reaction_role_subcommand.command(name="single", description="Create a single choice only reaction role")
    @commands_ext.has_permissions(manage_roles=True)
    @commands_ext.guild_only()
    @is_blocked()
    @analytics("create_reaction_role single")
    async def create_reaction_role_single(self, interaction: discord.ApplicationContext, message: str, role: discord.Role,
                                          role_2: discord.Role = None, role_3: discord.Role = None,
                                          role_4: discord.Role = None, role_5: discord.Role = None) -> None:
        view = self.create_view('s', [role, role_2, role_3, role_4, role_5])

        await interaction.channel.send(content=message, view=view)
        await interaction.response.send_message("Reaction role has been created!", ephemeral=True)

    @discord.Cog.listener()
    @is_blocked()
    async def on_interaction(self, interaction: discord.ApplicationContext) -> None:
        if interaction.type != discord.InteractionType.component:
            return

        split = interaction.custom_id.split('-')
        if len(split) != 2:
            return

        if split[0] not in ['rrn', 'rra', 'rrr', 'rrs']:
            return

        if not split[1].isdigit():
            return

        role = interaction.guild.get_role(int(split[1]))
        if role is None:
            return

        if split[0] == "rrn":
            if role in interaction.user.roles:
                await interaction.response.send_message(f"Role {role.mention} has been removed from you!",
                                                        ephemeral=True)
                await interaction.user.remove_roles(role, reason="Reaction role")
                return
            if role not in interaction.user.roles:
                await interaction.response.send_message(f"Role {role.mention} has been added to you!", ephemeral=True)
                await interaction.user.add_roles(role, reason="Reaction role")
                return

        if split[0] == "rra":
            if role in interaction.user.roles:
                await interaction.response.send_message(f"You already have this role!", ephemeral=True)
                return
            if role not in interaction.user.roles:
                await interaction.response.send_message(f"Role {role.mention} has been added to you!", ephemeral=True)
                await interaction.user.add_roles(role, reason="Reaction role")
                return

        if split[0] == "rrr":
            if role not in interaction.user.roles:
                await interaction.response.send_message(f"You do not have this role!", ephemeral=True)
                return
            if role in interaction.user.roles:
                await interaction.response.send_message(f"Role {role.mention} has been removed from you!",
                                                        ephemeral=True)
                await interaction.user.remove_roles(role, reason="Reaction role")
                return

        if split[0] == "rrs":
            if role in interaction.user.roles:
                await interaction.response.send_message(f"You already have selected {role.mention}", ephemeral=True)
                return

            roles = get_roles(interaction.message)
            await interaction.response.send_message(f"Role {role.mention} has been added to you!", ephemeral=True)
            await interaction.user.remove_roles(*roles, reason="Reaction role")
            await interaction.user.add_roles(role, reason="Reaction role")
