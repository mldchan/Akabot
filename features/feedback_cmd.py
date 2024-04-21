import discord

from database import conn as db
from utils.analytics import analytics
from utils.blocked import is_blocked


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


class SupportCmd(discord.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command(name="support", help="Get support for the bot")
    @is_blocked()
    @analytics("support")
    async def feedback(self, ctx: discord.Interaction):
        await ctx.response.send_message(
            "You can get support [here](<https://mldkyt.com/forumsrules?go=https://mldkyt.com/forums/viewforum.php?f"
            "=15>)")

    @discord.slash_command(name="website", help="Get the website link")
    @is_blocked()
    @analytics("website")
    async def website(self, ctx: discord.Interaction):
        await ctx.response.send_message("You can visit the website [here](<https://mldkyt.com/project/femboybot>)")

    feedback_subcommand = discord.SlashCommandGroup(name="feedback", description="Give feedback for the bot")

    @feedback_subcommand.command(name="bug", description="Report a bug")
    @is_blocked()
    @analytics("feedback bug")
    async def report_bug(self, ctx: discord.Interaction, bug: str):
        add_feature_report('bug', ctx.user.id, bug)
        await ctx.response.send_message("Thank you for reporting the bug!")

    @feedback_subcommand.command(name="feature", description="Suggest a feature")
    @is_blocked()
    @analytics("feedback feature")
    async def suggest_feature(self, ctx: discord.Interaction, feature: str):
        add_feature_report('feature', ctx.user.id, feature)
        await ctx.response.send_message("Thank you for suggesting the feature!")
