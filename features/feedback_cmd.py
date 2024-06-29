import logging

import discord
from discord.ui.input_text import InputText
from discord.ui.item import Item
from discord.ext import commands as cmds_ext

from database import conn as db
from utils.analytics import analytics
from utils.blocked import is_blocked

import requests

def db_init():
    cur = db.cursor()
    logger = logging.getLogger("Akatsuki")
    logger.debug("Creating table for feature reports :3")
    cur.execute('create table if not exists feature_reports (type text, user_id int, feature text)')
    cur.close()
    db.commit()


def add_feature_report(type: str, user_id: int, feature: str):
    db_init()
    logger = logging.getLogger("Akatsuki")
    cur = db.cursor()
    logger.debug(f"Adding {type} report from {user_id}: {feature}")
    cur.execute('create table if not exists feature_reports (type text, user_id int, feature text)')
    cur.execute('insert into feature_reports (type, user_id, feature) values (?, ?, ?)', (type, user_id, feature))
    cur.close()
    db.commit()


class VoteView(discord.ui.View):
    def __init__(self):
        super().__init__()

        button1 = discord.ui.Button(label="top.gg", url="https://top.gg/bot/1172922944033411243")

        self.add_item(button1)

class PrivacyPolicyView(discord.ui.View):
    def __init__(self):
        super().__init__()

        button1 = discord.ui.Button(label="akatsuki.nekoweb.org", url="https://akatsuki.nekoweb.org/project/akabot/privacy/")

        self.add_item(button1)

class BugReportModal(discord.ui.Modal):
    def __init__(self, gh_info: dict) -> None:
        super().__init__(title="Bug Report", timeout=600)

        self.gh_info = gh_info

        self.title_input = InputText(label="Title", style=discord.InputTextStyle.short, max_length=100, min_length=8, required=True)
        self.description_input = InputText(label="Description", style=discord.InputTextStyle.long, max_length=1000, min_length=20, required=True)

        self.add_item(self.title_input)
        self.add_item(self.description_input)

    async def callback(self, interaction: discord.Interaction):
        requests.post(f"https://api.github.com/repos/{self.gh_info['git_user']}/{self.gh_info['git_repo']}/issues", headers={
            "Authorization": f"token {self.gh_info['token']}",
            "Accept": "application/vnd.github.v3+json"
        }, json={
            "title": self.title_input.value,
            "body": self.description_input.value,
            "labels": ["bug", "in-bot"]
        })

        await interaction.respond("Bug report submitted!", ephemeral=True)


class FeatureModal(discord.ui.Modal):
    def __init__(self, gh_info: dict) -> None:
        super().__init__(title="Feature Request", timeout=600)

        self.gh_info = gh_info

        self.title_input = InputText(label="Title", style=discord.InputTextStyle.short, max_length=100, min_length=8, required=True)
        self.description_input = InputText(label="Description", style=discord.InputTextStyle.long, max_length=1000, min_length=20, required=True)

        self.add_item(self.title_input)
        self.add_item(self.description_input)

    async def callback(self, interaction: discord.Interaction):
        requests.post(f"https://api.github.com/repos/{self.gh_info['git_user']}/{self.gh_info['git_repo']}/issues", headers={
            "Authorization": f"token {self.gh_info['token']}",
            "Accept": "application/vnd.github.v3+json"
        }, json={
            "title": self.title_input.value,
            "body": self.description_input.value,
            "labels": ["enhancement", "in-bot"]
        })

        await interaction.respond("Feature request submitted!", ephemeral=True)


class SupportCmd(discord.Cog):
    def __init__(self, bot: discord.Bot, gh_info: dict):
        self.bot = bot
        self.gh_info = gh_info

    @discord.slash_command(name="website", help="Get the website link")
    @is_blocked()
    @analytics("website")
    async def website(self, ctx: discord.ApplicationContext):
        await ctx.respond(
            "You can visit the website [here](<https://akatsuki.nekoweb.org/project/akabot>)") 
    
    @discord.slash_command(name="vote", description="Vote on the bot")
    @is_blocked()
    @analytics("vote")
    async def vote(self, ctx: discord.ApplicationContext):
        await ctx.respond(
            "You can click the button below to vote:",
            view=VoteView(),
            ephemeral=True
        )

    @discord.slash_command(name="privacy", description="Privacy policy URL")
    @is_blocked()
    @analytics("privacy policy")
    async def privacy_policy(str, ctx: discord.ApplicationContext):
        await ctx.respond(
            "You can click the button below to view the Privacy Policy:",
            view=PrivacyPolicyView(),
            ephemeral=True
        )

    @discord.slash_command(name="donate", description="Donate to the bot to support it")
    @is_blocked()
    @analytics("donate")
    async def donate(self, ctx: discord.ApplicationContext):
        await ctx.respond("You can donate to the bot [here](<https://ko-fi.com/akatsuki2555>)", ephemeral=True)

    @discord.slash_command(name="changelog", description="Get the bot's changelog")
    @is_blocked()
    @analytics("changelog")
    async def changelog(self, ctx: discord.ApplicationContext):
        with open("LATEST.md", "r") as f:
            changelog = f.read()
        
        await ctx.respond(changelog, ephemeral=True)

    feedback_subcommand = discord.SlashCommandGroup(name="feedback", description="Give feedback for the bot")

    @feedback_subcommand.command(name="bug", description="Report a bug")
    @cmds_ext.cooldown(1, 300, cmds_ext.BucketType.user)
    @is_blocked()
    @analytics("feedback bug")
    async def report_bug(self, ctx: discord.ApplicationContext):
        modal = BugReportModal(self.gh_info)
        await ctx.response.send_modal(modal)

    @feedback_subcommand.command(name="feature", description="Suggest a feature")
    @cmds_ext.cooldown(1, 300, cmds_ext.BucketType.user)
    @is_blocked()
    @analytics("feedback feature")
    async def suggest_feature(self, ctx: discord.ApplicationContext):
        modal = FeatureModal(self.gh_info)
        await ctx.response.send_modal(modal)
