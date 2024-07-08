import discord
from discord.ui.input_text import InputText
from discord.ui.item import Item
from discord.ext import commands as cmds_ext

from database import conn as db
from utils.analytics import analytics
from utils.blocked import is_blocked

import requests

from utils.config import get_key


def db_init():
    cur = db.cursor()
    cur.execute('create table if not exists feature_reports (type text, user_id int, feature text)')
    cur.close()
    db.commit()


def add_feature_report(type: str, user_id: int, feature: str):
    db_init()
    cur = db.cursor()
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

        button1 = discord.ui.Button(label="akatsuki.nekoweb.org",
                                    url="https://akatsuki.nekoweb.org/project/akabot/privacy/")

        self.add_item(button1)


class BugReportModal(discord.ui.Modal):
    def __init__(self) -> None:
        super().__init__(title="Bug Report", timeout=600)

        self.title_input = InputText(label="Title", style=discord.InputTextStyle.short, max_length=100, min_length=8,
                                     required=True)
        self.description_input = InputText(label="Description", style=discord.InputTextStyle.long, max_length=1000,
                                           min_length=20, required=True)

        self.add_item(self.title_input)
        self.add_item(self.description_input)

    async def callback(self, interaction: discord.Interaction):
        issue_body = ("- This bug report was created by {display} ({user} {id}) on Discord\n\n"
                      "---\n\n"
                      "### The issue was described by the user as follows:\n\n"
                      "{desc}".format(display=interaction.user.display_name,
                                      user=interaction.user.name,
                                      id=interaction.user.id,
                                      desc=self.description_input.value))

        git_user = get_key("GitHub_User")
        git_repo = get_key("GitHub_Repo")
        token = get_key("GitHub_Token")
        requests.post(f"https://api.github.com/repos/{git_user}/{git_repo}/issues",
                      headers={
                          "Authorization": f"token {token}",
                          "Accept": "application/vnd.github.v3+json"
                      },
                      json={
                          "title": "Bug Report: {bug}".format(bug=self.title_input.value),
                          "body": issue_body,
                          "labels": ["bug", "in-bot"]
                      })

        await interaction.respond("Bug report submitted!", ephemeral=True)


class FeatureModal(discord.ui.Modal):
    def __init__(self) -> None:
        super().__init__(title="Feature Request", timeout=600)
        self.title_input = InputText(label="Title", style=discord.InputTextStyle.short, max_length=100, min_length=8,
                                     required=True)
        self.description_input = InputText(label="Description", style=discord.InputTextStyle.long, max_length=1000,
                                           min_length=20, required=True)

        self.add_item(self.title_input)
        self.add_item(self.description_input)

    async def callback(self, interaction: discord.Interaction):
        issue_body = ("- This feature request was created by {display} ({user} {id}) on Discord\n\n"
                      "---\n\n"
                      "### The issue was described by the user as follows:\n\n"
                      "{desc}".format(display=interaction.user.display_name,
                                      user=interaction.user.name,
                                      id=interaction.user.id,
                                      desc=self.description_input.value))

        git_user = get_key("GitHub_User")
        git_repo = get_key("GitHub_Repo")
        token = get_key("GitHub_Token")
        requests.post(f"https://api.github.com/repos/{git_user}/{git_repo}/issues",
                      headers={
                          "Authorization": f"token {token}",
                          "Accept": "application/vnd.github.v3+json"
                      },
                      json={
                          "title": "Feature request: {title}".format(title=self.title_input.value),
                          "body": issue_body,
                          "labels": ["enhancement", "in-bot"]
                      })

        await interaction.respond("Feature request submitted!", ephemeral=True)


class ConfirmSubmitBugReport(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="I agree and want to submit", style=discord.ButtonStyle.primary)
    async def submit(self, button: discord.ui.Button, interaction: discord.Interaction):
        modal = BugReportModal()
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="I don't agree and prefer to submit on GitHub", style=discord.ButtonStyle.secondary)
    async def cancel_gh(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.disable_all_items()
        await interaction.respond(
            "You can open a bug report on the [GitHub repository](https://github.com/Akatsuki2555/Akabot/issues/new) directly.",
            ephemeral=True)


class ConfirmSubmitFeatureRequest(discord.ui.View):
    def __init__(self):
        super().__init__()

    @discord.ui.button(label="I agree and want to submit", style=discord.ButtonStyle.primary)
    async def submit(self, button: discord.ui.Button, interaction: discord.Interaction):
        modal = FeatureModal()
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="I don't agree and prefer to submit on GitHub", style=discord.ButtonStyle.secondary)
    async def cancel_gh(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.respond(
            "You can open a feature request on the [GitHub repository](https://github.com/Akatsuki2555/Akabot/issues/new) directly.",
            ephemeral=True)


class SupportCmd(discord.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

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
    async def privacy_policy(self, ctx: discord.ApplicationContext):
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
        await ctx.respond(content="## Notice before submitting a bug report\n"
                                  "If you do submit a bug report, the following information will be sent to GitHub issues:\n"
                                  "- Your Discord display name, username and ID\n"
                                  "- Any information you provide in the title and description in the form\n"
                                  "\n"
                                  "If you don't agree with this, you can open a bug report on the GitHub repository directly.\n"
                                  "*This was done to prevent spam and abuse of the bug report system.*\n"
                                  "*If you don't want to submit at all, you can completely ignore this message.*",
                          ephemeral=True,
                          view=ConfirmSubmitBugReport())

    @feedback_subcommand.command(name="feature", description="Suggest a feature")
    @cmds_ext.cooldown(1, 300, cmds_ext.BucketType.user)
    @is_blocked()
    @analytics("feedback feature")
    async def suggest_feature(self, ctx: discord.ApplicationContext):
        await ctx.respond(content="## Notice before submitting a feature request\n"
                                  "If you do submit a feature request, the following information will be sent to GitHub issues:\n"
                                  "- Your Discord display name, username and ID\n"
                                  "- Any information you provide in the title and description in the form\n"
                                  "\n"
                                  "If you don't agree with this, you can open a feature request on the GitHub repository directly.\n"
                                  "*This was done to prevent spam and abuse of the feature request system.*\n"
                                  "*If you don't want to submit at all, you can completely ignore this message.*",
                          ephemeral=True,
                          view=ConfirmSubmitFeatureRequest())
