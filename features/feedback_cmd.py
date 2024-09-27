import asyncio

import aiohttp
import discord
from discord.ext import commands as cmds_ext
from discord.ui.input_text import InputText

from utils.analytics import analytics
from utils.config import get_key
from utils.languages import get_translation_for_key_localized as trl


class VoteView(discord.ui.View):
    def __init__(self):
        super().__init__()

        button1 = discord.ui.Button(label="top.gg", url="https://top.gg/bot/1172922944033411243")

        self.add_item(button1)


class PrivacyPolicyView(discord.ui.View):
    def __init__(self):
        super().__init__()

        button1 = discord.ui.Button(label="akatsuki2555.is-a.dev",
                                    url="https://akatsuki2555.is-a.dev/project/akabot/privacy/")

        self.add_item(button1)


class BugReportModal(discord.ui.Modal):
    def __init__(self, user_id: int) -> None:
        super().__init__(title="Bug Report", timeout=600)

        self.user_id = user_id
        title = asyncio.run(trl(user_id, 0, "title"))
        description = asyncio.run(trl(user_id, 0, "description"))
        self.title_input = InputText(label=title, style=discord.InputTextStyle.short, max_length=100, min_length=8,
                                     required=True)
        self.description_input = InputText(label=description, style=discord.InputTextStyle.long, max_length=1000,
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
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        data = {
            "title": "Bug Report: {bug}".format(bug=self.title_input.value),
            "body": issue_body,
            "labels": ["bug", "in-bot"]
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(f"https://api.github.com/repos/{git_user}/{git_repo}/issues", headers=headers, json=data) as response:
                if response.status != 201:
                    await interaction.response.send_message(f"Failed to submit bug report: {await response.text()}", ephemeral=True)
                    return
        await interaction.response.send_message(await trl(self.user_id, 0, "feedback_bug_report_submitted", append_tip=True), ephemeral=True)


class FeatureModal(discord.ui.Modal):
    def __init__(self, user_id: int) -> None:
        self.user_id = user_id
        super().__init__(title=asyncio.run(trl(user_id, 0, "feedback_feature_form_title")), timeout=600)

        title = asyncio.run(trl(user_id, 0, "title"))
        description = asyncio.run(trl(user_id, 0, "description"))
        self.title_input = InputText(label=title, style=discord.InputTextStyle.short, max_length=100, min_length=8,
                                     required=True)
        self.description_input = InputText(label=description, style=discord.InputTextStyle.long, max_length=1000,
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
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        data = {
            "title": "Feature request: {title}".format(title=self.title_input.value),
            "body": issue_body,
            "labels": ["enhancement", "in-bot"]
        }
        async with aiohttp.ClientSession() as session:
            async with session.post(f"https://api.github.com/repos/{git_user}/{git_repo}/issues", headers=headers, json=data) as response:
                if response.status != 201:
                    await interaction.response.send_message(f"Failed to submit feature request: {await response.text()}", ephemeral=True)
                    return
        await interaction.response.send_message(await trl(self.user_id, 0, "feedback_feature_submitted", append_tip=True), ephemeral=True)


class ConfirmSubmitBugReport(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__()
        self.user_id = user_id

        self.agree_button = discord.ui.Button(label=asyncio.run(trl(user_id, 0, "feedback_agree")))
        self.agree_button.callback = self.submit
        self.add_item(self.agree_button)

        self.cancel_github = discord.ui.Button(label=asyncio.run(trl(user_id, 0, "feedback_prefer_github")),
                                               style=discord.ButtonStyle.secondary)
        self.cancel_github.callback = self.cancel_gh
        self.add_item(self.cancel_github)

    async def submit(self, button: discord.ui.Button, interaction: discord.Interaction):
        modal = BugReportModal(self.user_id)
        await interaction.response.send_modal(modal)

    async def cancel_gh(self, button: discord.ui.Button, interaction: discord.Interaction):
        self.disable_all_items()
        await interaction.respond(
            await trl(self.user_id, 0, "feedback_bug_report_direct", append_tip=True),
            ephemeral=True)


class ConfirmSubmitFeatureRequest(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__()
        self.user_id = user_id

        self.agree_button = discord.ui.Button(label=asyncio.run(trl(user_id, 0, "feedback_agree")))
        self.agree_button.callback = self.submit
        self.add_item(self.agree_button)

        self.cancel_github = discord.ui.Button(label=asyncio.run(trl(user_id, 0, "feedback_prefer_github")),
                                               style=discord.ButtonStyle.secondary)
        self.cancel_github.callback = self.cancel_gh
        self.add_item(self.cancel_github)

    async def submit(self, button: discord.ui.Button, interaction: discord.Interaction):
        modal = FeatureModal(self.user_id)
        await interaction.response.send_modal(modal)

    async def cancel_gh(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.respond(
            await trl(self.user_id, 0, "feedback_feature_direct", append_tip=True),
            ephemeral=True)


class SupportCmd(discord.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    @discord.slash_command(name="website", help="Get the website link")
    @analytics("website")
    async def website(self, ctx: discord.ApplicationContext):
        await ctx.respond(await trl(ctx.user.id, ctx.guild.id, "feedback_visit_website", append_tip=True), ephemeral=True)

    @discord.slash_command(name="vote", description="Vote on the bot")
    @analytics("vote")
    async def vote(self, ctx: discord.ApplicationContext):
        await ctx.respond(
            await trl(ctx.user.id, ctx.guild.id, "feedback_vote", append_tip=True),
            view=VoteView(),
            ephemeral=True
        )

    @discord.slash_command(name="privacy", description="Privacy policy URL")
    @analytics("privacy policy")
    async def privacy_policy(self, ctx: discord.ApplicationContext):
        await ctx.respond(
            await trl(ctx.user.id, ctx.guild.id, "feedback_privacy_policy", append_tip=True),
            view=PrivacyPolicyView(),
            ephemeral=True
        )

    @discord.slash_command(name="donate", description="Donate to the bot to support it")
    @analytics("donate")
    async def donate(self, ctx: discord.ApplicationContext):
        await ctx.respond(await trl(ctx.user.id, ctx.guild.id, "feedback_donate", append_tip=True), ephemeral=True)

    @discord.slash_command(name="changelog", description="Get the bot's changelog")
    @discord.option(name="version", description="The version to get the changelog for", choices=["3.3", "3.2", "3.1"])
    @analytics("changelog")
    async def changelog(self, ctx: discord.ApplicationContext, version: str = get_key("Bot_Version", "3.3")):
        if version == "3.4":
            with open("LATEST.md", "r") as f:
                changelog = f.read()

            await ctx.respond(changelog, ephemeral=True)
        elif version == "3.3":
            with open("LATEST_3.3.md", "r") as f:
                changelog = f.read()

            await ctx.respond(changelog, ephemeral=True)
        elif version == "3.2":
            with open("LATEST_3.2.md", "r") as f:
                changelog = f.read()

            await ctx.respond(changelog, ephemeral=True)
        elif version == "3.1":
            with open("LATEST_3.1.md", "r") as f:
                changelog = f.read()

            await ctx.respond(changelog, ephemeral=True)
        else:
            await ctx.respond(await trl(ctx.user.id, ctx.guild.id, "feedback_changelog_invalid_version"), ephemeral=True)

    feedback_subcommand = discord.SlashCommandGroup(name="feedback", description="Give feedback for the bot")

    @feedback_subcommand.command(name="bug", description="Report a bug")
    @cmds_ext.cooldown(1, 300, cmds_ext.BucketType.user)
    @analytics("feedback bug")
    async def report_bug(self, ctx: discord.ApplicationContext):
        await ctx.respond(content=await trl(ctx.user.id, ctx.guild.id, "feedback_bug_report_disclaimer", append_tip=True),
                          ephemeral=True,
                          view=ConfirmSubmitBugReport(ctx.user.id))

    @feedback_subcommand.command(name="feature", description="Suggest a feature")
    @cmds_ext.cooldown(1, 300, cmds_ext.BucketType.user)
    @analytics("feedback feature")
    async def suggest_feature(self, ctx: discord.ApplicationContext):
        await ctx.respond(content=await trl(ctx.user.id, ctx.guild.id, "feedback_feature_disclaimer", append_tip=True),
                          ephemeral=True,
                          view=ConfirmSubmitFeatureRequest(ctx.user.id))

    @discord.slash_command(name="about", description="Get information about the bot")
    @analytics("about")
    async def about(self, ctx: discord.ApplicationContext):
        await ctx.respond(await trl(ctx.user.id, ctx.guild.id, "feedback_about", append_tip=True), ephemeral=True)
