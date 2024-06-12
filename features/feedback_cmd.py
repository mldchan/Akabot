import logging

import discord
from discord.ui.item import Item

from database import conn as db
from utils.analytics import analytics
from utils.blocked import is_blocked


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

class SupportCmd(discord.Cog):
    def __init__(self, bot):
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
    async def privacy_policy(str, ctx: discord.ApplicationContext):
        await ctx.respond(
            "You can click the button below to view the Privacy Policy:",
            view=PrivacyPolicyView(),
            ephemeral=True
        )

    feedback_subcommand = discord.SlashCommandGroup(name="feedback", description="Give feedback for the bot")

    @feedback_subcommand.command(name="bug", description="Report a bug")
    @is_blocked()
    @analytics("feedback bug")
    async def report_bug(self, ctx: discord.ApplicationContext, bug: str):
        add_feature_report('bug', ctx.user.id, bug)
        await ctx.respond("Thank you for reporting the bug!")

    @feedback_subcommand.command(name="feature", description="Suggest a feature")
    @is_blocked()
    @analytics("feedback feature")
    async def suggest_feature(self, ctx: discord.ApplicationContext, feature: str):
        add_feature_report('feature', ctx.user.id, feature)
        await ctx.respond("Thank you for suggesting the feature!")
