import discord
from discord.ext import commands as commands_ext
from utils.blocked import is_blocked

def get_roles(msg: discord.Message):
    roles = []
    
    if msg.guild is None:
        return []
    
    for i in msg.components:
        if not isinstance(i, discord.ActionRow):
            print('is not actionrow')
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
        
    create_reaction_role_subcommand = discord.SlashCommandGroup(name="create_reaction_role", description="Create a reaction role")
    
    @create_reaction_role_subcommand.command(name="normal", description="Create a normal reaction role")
    @commands_ext.has_permissions(manage_roles=True)
    @commands_ext.guild_only()
    @is_blocked()
    async def create_reaction_role_normal(self, interaction: discord.Interaction, message: str, role: discord.Role, role_2: discord.Role = None, role_3: discord.Role = None, role_4: discord.Role = None, role_5: discord.Role = None) -> None:
        view = discord.ui.View()
        view.add_item(discord.ui.Button(style=discord.ButtonStyle.primary, label=role.name, custom_id=f"rrn-{role.id}"))
        if role_2 is not None:
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.primary, label=role_2.name, custom_id=f"rrn-{role_2.id}"))
        if role_3 is not None:
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.primary, label=role_3.name, custom_id=f"rrn-{role_3.id}"))
        if role_4 is not None:
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.primary, label=role_4.name, custom_id=f"rrn-{role_4.id}"))
        if role_5 is not None:
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.primary, label=role_5.name, custom_id=f"rrn-{role_5.id}"))
            
        await interaction.channel.send(content=message, view=view)
        await interaction.response.send_message("Reaction role has been created!", ephemeral=True)
        
        
    @create_reaction_role_subcommand.command(name="add_only", description="Create an add only reaction role")
    @commands_ext.has_permissions(manage_roles=True)
    @commands_ext.guild_only()
    @is_blocked()
    async def create_reaction_role_add(self, interaction: discord.Interaction, message: str, role: discord.Role, role_2: discord.Role = None, role_3: discord.Role = None, role_4: discord.Role = None, role_5: discord.Role = None) -> None:
        view = discord.ui.View()
        view.add_item(discord.ui.Button(style=discord.ButtonStyle.primary, label=role.name, custom_id=f"rra-{role.id}"))
        if role_2 is not None:
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.primary, label=role_2.name, custom_id=f"rra-{role_2.id}"))
        if role_3 is not None:
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.primary, label=role_3.name, custom_id=f"rra-{role_3.id}"))
        if role_4 is not None:
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.primary, label=role_4.name, custom_id=f"rra-{role_4.id}"))
        if role_5 is not None:
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.primary, label=role_5.name, custom_id=f"rra-{role_5.id}"))
            
        await interaction.channel.send(content=message, view=view)
        await interaction.response.send_message("Reaction role has been created!", ephemeral=True)
        
    @create_reaction_role_subcommand.command(name="remove_only", description="Create a remove only reaction role")
    @commands_ext.has_permissions(manage_roles=True)
    @commands_ext.guild_only()
    @is_blocked()
    async def create_reaction_role_remove(self, interaction: discord.Interaction, message: str, role: discord.Role, role_2: discord.Role = None, role_3: discord.Role = None, role_4: discord.Role = None, role_5: discord.Role = None) -> None:
        view = discord.ui.View()
        view.add_item(discord.ui.Button(style=discord.ButtonStyle.primary, label=role.name, custom_id=f"rrr-{role.id}"))
        if role_2 is not None:
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.primary, label=role_2.name, custom_id=f"rrr-{role_2.id}"))
        if role_3 is not None:
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.primary, label=role_3.name, custom_id=f"rrr-{role_3.id}"))
        if role_4 is not None:
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.primary, label=role_4.name, custom_id=f"rrr-{role_4.id}"))
        if role_5 is not None:
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.primary, label=role_5.name, custom_id=f"rrr-{role_5.id}"))
            
        await interaction.channel.send(content=message, view=view)
        await interaction.response.send_message("Reaction role has been created!", ephemeral=True)
        
        
    @create_reaction_role_subcommand.command(name="single", description="Create a single choice only reaction role")
    @commands_ext.has_permissions(manage_roles=True)
    @commands_ext.guild_only()
    @is_blocked()
    async def create_reaction_role_single(self, interaction: discord.Interaction, message: str, role: discord.Role, role_2: discord.Role = None, role_3: discord.Role = None, role_4: discord.Role = None, role_5: discord.Role = None) -> None:
        view = discord.ui.View()
        view.add_item(discord.ui.Button(style=discord.ButtonStyle.primary, label=role.name, custom_id=f"rrs-{role.id}"))
        if role_2 is not None:
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.primary, label=role_2.name, custom_id=f"rrs-{role_2.id}"))
        if role_3 is not None:
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.primary, label=role_3.name, custom_id=f"rrs-{role_3.id}"))
        if role_4 is not None:
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.primary, label=role_4.name, custom_id=f"rrs-{role_4.id}"))
        if role_5 is not None:
            view.add_item(discord.ui.Button(style=discord.ButtonStyle.primary, label=role_5.name, custom_id=f"rrs-{role_5.id}"))
            
        await interaction.channel.send(content=message, view=view)
        await interaction.response.send_message("Reaction role has been created!", ephemeral=True)
    
    @discord.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction) -> None:
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
                await interaction.response.send_message(f"Role {role.mention} has been removed from you!", ephemeral=True)
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
                await interaction.response.send_message(f"Role {role.mention} has been removed from you!", ephemeral=True)
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