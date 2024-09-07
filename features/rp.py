
import json
import random
import discord


def pick_hug_gif():
    with open("configs/rp.json", "r") as f:
        data = json.load(f)
    return random.choice(data["hug_gifs"])

def pick_kiss_yaoi_gif():
    with open("configs/rp.json", "r") as f:
        data = json.load(f)
    return random.choice(data["kiss_yaoi_gifs"])

def pick_kiss_yuri_gif():
    with open("configs/rp.json", "r") as f:
        data = json.load(f)
    return random.choice(data["kiss_yuri_gifs"])

def pick_bite_gif():
    with open("configs/rp.json", "r") as f:
        data = json.load(f)
    return random.choice(data["bite_gifs"])

def get_footer_msg():
    footers = [
        "This feature is still in development",
        "Drop suggestions using /feedback suggest",
        "Drop gif suggestions in #akabot-suggestions in the support server",
        "Please be respectful to everyone in the server",
    ]
    
    return random.choice(footers)

def get_unbite_img():
    with open("configs/rp.json", "r") as f:
        data = json.load(f)
    return data["unbite_img"]

class RoleplayCommands(discord.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    rp_group = discord.SlashCommandGroup("rp", "Roleplay commands")
    
    @rp_group.command(name="hug")
    async def hug(self, ctx, member: discord.Member):
        """Hug a member"""
        gif = pick_hug_gif()
        embed = discord.Embed(title=f"{ctx.author.display_name} hugs {member.display_name}!", footer=discord.EmbedFooter(text=get_footer_msg()))
        embed.set_image(url=gif)
        await ctx.respond(content=f"{ctx.author.mention} hugs {member.mention}!", embed=embed)

    @rp_group.command(name="kiss")
    async def kiss(self, ctx, member: discord.Member):
        """Kiss a member"""
        gif = pick_kiss_yaoi_gif()
        embed = discord.Embed(title=f"{ctx.author.display_name} kisses {member.display_name}!", footer=discord.EmbedFooter(text=get_footer_msg()))
        embed.set_image(url=gif)
        await ctx.respond(content=f"{ctx.author.mention} kisses {member.mention}!", embed=embed)

    @rp_group.command(name="bite")
    async def bite(self, ctx, member: discord.Member):
        """Bite a member"""
        gif = pick_bite_gif()
        embed = discord.Embed(title=f"{ctx.author.display_name} bites {member.display_name}!", footer=discord.EmbedFooter(text=get_footer_msg()))
        embed.set_image(url=gif)
        await ctx.respond(content=f"{ctx.author.mention} bites {member.mention}!", embed=embed)
        
    @rp_group.command(name="unbite")
    async def unbite(self, ctx, member: discord.Member):
        """Unbite a member"""
        embed = discord.Embed(title=f"{ctx.author.display_name} unbites {member.display_name}!", footer=discord.EmbedFooter(text=get_footer_msg()))
        embed.set_image(url=get_unbite_img())
        await ctx.respond(content=f"{ctx.author.mention} unbites {member.mention}!", embed=embed)

