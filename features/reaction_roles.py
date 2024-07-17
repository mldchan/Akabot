import discord
from discord.ext import commands as commands_ext

from utils.analytics import analytics
from utils.blocked import is_blocked
from utils.languages import get_translation_for_key_localized as trl


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

    reaction_roles_subcommand = discord.SlashCommandGroup(name="reaction_roles",
                                                          description="Create a reaction role")

    def create_view(self, type: str, roles: list[discord.Role]) -> discord.ui.View:
        view = discord.ui.View()
        for role in roles:
            if role is None:
                continue

            view.add_item(
                discord.ui.Button(style=discord.ButtonStyle.primary, label=role.name, custom_id=f"rr{type}-{role.id}"))

        return view

    @reaction_roles_subcommand.command(name="create", description="Create a reaction role")
    @discord.default_permissions(manage_roles=True)
    @discord.option(name="type", description="Type of reaction role",
                    choices=["normal", "add only", "remove only", "single"])
    @commands_ext.has_permissions(manage_roles=True)
    @commands_ext.guild_only()
    @commands_ext.bot_has_permissions(send_messages=True)
    @is_blocked()
    @analytics("create_reaction_role")
    async def create_reaction_role(self, interaction: discord.ApplicationContext, type: str, message: str,
                                   role_1: discord.Role, role_2: discord.Role = None, role_3: discord.Role = None,
                                   role_4: discord.Role = None, role_5: discord.Role = None,
                                   role_6: discord.Role = None,
                                   role_7: discord.Role = None, role_8: discord.Role = None,
                                   role_9: discord.Role = None,
                                   role_10: discord.Role = None) -> None:
        if type == "single":
            type = "s"
        elif type == "add only":
            type = "a"
        elif type == "remove only":
            type = "r"
        else:
            type = "n"

        roles = [role_1, role_2, role_3, role_4, role_5, role_6, role_7, role_8, role_9, role_10]
        view = self.create_view(type, roles)

        await interaction.channel.send(content=message, view=view)
        await interaction.response.send_message("Reaction role has been created!", ephemeral=True)

    @reaction_roles_subcommand.command(name="edit", description="Edit a reaction role")
    @discord.default_permissions(manage_roles=True)
    @discord.option(name="message", description="Message to edit")
    @discord.option(name="type", description="Type of reaction role",
                    choices=["normal", "add only", "remove only", "single"])
    @commands_ext.has_permissions(manage_roles=True)
    @commands_ext.guild_only()
    @commands_ext.bot_has_permissions(send_messages=True)
    @is_blocked()
    @analytics("edit_reaction_role")
    async def edit_reaction_role(self, interaction: discord.ApplicationContext, message: str, type: str,
                                 role_1: discord.Role, role_2: discord.Role = None, role_3: discord.Role = None,
                                 role_4: discord.Role = None, role_5: discord.Role = None, role_6: discord.Role = None,
                                 role_7: discord.Role = None, role_8: discord.Role = None, role_9: discord.Role = None,
                                 role_10: discord.Role = None, content: str = None) -> None:
        if not message.isdigit():
            await interaction.response.send_message(
                trl(interaction.user.id, interaction.guild.id, "reaction_roles_edit_id_must_be_a_number"),
                ephemeral=True)
            return

        if type == "single":
            type = "s"
        elif type == "add only":
            type = "a"
        elif type == "remove only":
            type = "r"
        else:
            type = "n"

        roles = [role_1, role_2, role_3, role_4, role_5, role_6, role_7, role_8, role_9, role_10]
        view = self.create_view(type, roles)

        msg = await interaction.channel.fetch_message(int(message))
        if msg is None:
            await interaction.response.send_message(
                trl(interaction.user.id, interaction.guild.id, "reaction_roles_edit_msg_not_found"), ephemeral=True)
            return

        if not content:
            await msg.edit(view=view)
        else:
            await msg.edit(content=content, view=view)

        await interaction.response.send_message(
            trl(interaction.user.id, interaction.guild.id, "reaction_roles_edited_response"), ephemeral=True)

    @discord.Cog.listener()
    @is_blocked()
    async def on_interaction(self, interaction: discord.Interaction) -> None:
        if interaction.type != discord.InteractionType.component:
            return

        if not interaction.guild.me.guild_permissions.manage_roles:
            await interaction.response.send_message(
                trl(interaction.user.id, interaction.guild.id, "reaction_roles_no_perm"),
                ephemeral=True)
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

        if role.position >= interaction.guild.me.top_role.position:
            await interaction.response.send_message(
                trl(interaction.user.id, interaction.guild.id, "reaction_roles_cant_assign_role"),
                ephemeral=True)
            return

        if split[0] == "rrn":
            if role in interaction.user.roles:
                await interaction.response.send_message(
                    trl(interaction.user.id, interaction.guild.id, "reaction_roles_role_removed").format(
                        mention=role.mention),
                    ephemeral=True)
                await interaction.user.remove_roles(role, reason="Reaction role")
                return
            if role not in interaction.user.roles:
                await interaction.response.send_message(
                    trl(interaction.user.id, interaction.guild.id, "reaction_roles_role_added").format(
                        mention=role.mention),
                    ephemeral=True)
                await interaction.user.add_roles(role, reason="Reaction role")
                return

        if split[0] == "rra":
            if role in interaction.user.roles:
                await interaction.response.send_message(
                    trl(interaction.user.id, interaction.guild.id, "reaction_roles_already_have"),
                    ephemeral=True)
                return
            if role not in interaction.user.roles:
                await interaction.response.send_message(
                    trl(interaction.user.id, interaction.guild.id, "reaction_roles_role_added").format(
                        mention=role.mention),
                    ephemeral=True)
                await interaction.user.add_roles(role, reason="Reaction role")
                return

        if split[0] == "rrr":
            if role not in interaction.user.roles:
                await interaction.response.send_message(
                    trl(interaction.user.id, interaction.guild.id, "reaction_roles_already_dont"),
                    ephemeral=True)
                return
            if role in interaction.user.roles:
                await interaction.response.send_message(
                    trl(interaction.user.id, interaction.guild.id, "reaction_roles_role_removed").format(
                        mention=role.mention),
                    ephemeral=True)
                await interaction.user.remove_roles(role, reason="Reaction role")
                return

        if split[0] == "rrs":
            if role in interaction.user.roles:
                await interaction.response.send_message(
                    trl(interaction.user.id, interaction.guild.id, "reaction_roles_already_selected").format(
                        mention=role.mention),
                    ephemeral=True)
                return

            roles = get_roles(interaction.message)
            await interaction.response.send_message(
                trl(interaction.user.id, interaction.guild.id, "reaction_roles_selected").format(mention=role.mention),
                ephemeral=True)
            await interaction.user.remove_roles(*roles, reason="Reaction role")
            await interaction.user.add_roles(role, reason="Reaction role")
