import os
import re
import discord
from discord import ui as dc_ui
from discord.ext import commands as dc_cmds
from database import conn as db
from utils.blocked import is_blocked


class Polls(discord.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        super().__init__()

        self.bot = bot

    @discord.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.component:
            return

        if re.match(r'^poll_[1-5]$', interaction.custom_id) is None:
            return

        if interaction.guild is None:
            return

        data = PollData(interaction.guild.id, interaction.message.id)
        if data.closed:
            await interaction.response.send_message("Poll is closed by an administrator.", ephemeral=True)
            return

        status = data.add_vote(interaction.user.id, int(interaction.custom_id.split('_')[1]))
        if status == "status:already_voted":
            await interaction.response.send_message("You have already voted!", ephemeral=True)
            return

        if status == "status:invalid_option":
            await interaction.response.send_message("Invalid option!", ephemeral=True)
            return

        await interaction.response.send_message(f"You have voted for `{status}`!", ephemeral=True)

    polls_subcommand = discord.SlashCommandGroup(name="polls", description="Create a poll")

    @polls_subcommand.command(name="create", description="Create a poll")
    @dc_cmds.guild_only()
    @dc_cmds.has_permissions(manage_guild=True)
    async def command_create_poll(self, ctx: discord.Interaction, question: str, ans1: str, ans2: str, ans3: str = "",
                                  ans4: str = "", ans5: str = ""):
        answers = [ans1, ans2]
        if ans3 != "":
            answers.append(ans3)
        if ans4 != "":
            answers.append(ans4)
        if ans5 != "":
            answers.append(ans5)

        poll = Poll(answers)
        msg = await ctx.channel.send(content=question, view=poll)

        data = PollData(ctx.guild.id, msg.id)
        data.set_question(question)
        data.set_answers(answers)
        data.save()

        await ctx.response.send_message("Poll has been created!", ephemeral=True)

    @polls_subcommand.command(name="info", description="Get info about a poll.")
    @dc_cmds.guild_only()
    @dc_cmds.has_permissions(manage_guild=True)
    @is_blocked()
    @discord.option(name="msg_link", description="The link to the poll message. Copy by right clicking the message.",
                    required=True)
    async def command_poll_info(self, ctx: discord.Interaction, msg_link: str):
        match = re.match(r'^https?://discord.com/channels/(\d+)/(\d+)/(\d+)$', msg_link)
        if match is None or len(match.groups()) != 3:
            await ctx.response.send_message("Invalid message link!", ephemeral=True)
            return

        cur = db.cursor()
        cur.execute("SELECT guild_id, message_id "
                    "FROM polls "
                    "WHERE guild_id = ? AND message_id = ?",
                    (match.group(1), match.group(3)))
        if not cur.fetchone():
            await ctx.response.send_message("Poll not found!", ephemeral=True)
            cur.close()
            return

        cur.close()

        data = PollData(match.group(1), match.group(3))
        message = f"""
**Question:** {data.question}

**Answers:**
1. {data.ans1} - {len(data.ans1_votes)} votes
2. {data.ans2} - {len(data.ans2_votes)} votes\n"""

        if data.answer_count >= 3:
            message += f"3. {data.ans3} - {len(data.ans3_votes)} votes\n"
        if data.answer_count >= 4:
            message += f"4. {data.ans4} - {len(data.ans4_votes)} votes\n"
        if data.answer_count >= 5:
            message += f"5. {data.ans5} - {len(data.ans5_votes)} votes\n"

        await ctx.response.send_message(message, ephemeral=True)

    @polls_subcommand.command(name="close", description="Close a poll.")
    @dc_cmds.guild_only()
    @dc_cmds.has_permissions(manage_guild=True)
    @is_blocked()
    @discord.option(name="msg_link", description="The link to the poll message. Copy by right clicking the message.",
                    required=True)
    async def command_close_poll(self, ctx: discord.Interaction, msg_link: str):
        match = re.match(r'^https?://discord.com/channels/(\d+)/(\d+)/(\d+)$', msg_link)
        if match is None or len(match.groups()) != 3:
            await ctx.response.send_message("Invalid message link!", ephemeral=True)
            return

        cur = db.cursor()
        cur.execute("SELECT guild_id, message_id "
                    "FROM polls "
                    "WHERE guild_id = ? AND message_id = ?",
                    (match.group(1), match.group(3)))
        if not cur.fetchone():
            await ctx.response.send_message("Poll not found!", ephemeral=True)
            cur.close()
            return

        cur.execute("UPDATE polls "
                    "SET closed = 1 "
                    "WHERE guild_id = ? AND message_id = ?", (match.group(1), match.group(3)))
        cur.close()
        db.commit()

        await ctx.response.send_message("Poll has been closed!", ephemeral=True)

    @polls_subcommand.command(name='reopen', description='Reopen a poll.')
    @dc_cmds.guild_only()
    @dc_cmds.has_permissions(manage_guild=True)
    @is_blocked()
    @discord.option(name='msg_link', description='The link to the poll message. Copy by right clicking the message.',
                    required=True)
    async def command_reopen_poll(self, ctx: discord.Interaction, msg_link: str):
        match = re.match(r'^https?://discord.com/channels/(\d+)/(\d+)/(\d+)$', msg_link)
        if match is None or len(match.groups()) != 3:
            await ctx.response.send_message('Invalid message link!', ephemeral=True)
            return

        cur = db.cursor()
        cur.execute('SELECT guild_id, message_id '
                    'FROM polls '
                    'WHERE guild_id = ? AND message_id = ?',
                    (match.group(1), match.group(3)))
        if not cur.fetchone():
            await ctx.response.send_message('Poll not found!', ephemeral=True)
            cur.close()
            return

        cur.execute('UPDATE polls '
                    'SET closed = 0 '
                    'WHERE guild_id = ? AND message_id = ?', (match.group(1), match.group(3)))
        cur.close()
        db.commit()

        await ctx.response.send_message('Poll has been reopened!', ephemeral=True)


class Poll(dc_ui.View):
    def __init__(self, answers: list[str]):
        super().__init__(timeout=None)

        for i in range(len(answers)):
            btn = dc_ui.Button(style=discord.ButtonStyle.primary, label=answers[i], custom_id=f'poll_{i + 1}')
            self.add_item(btn)


class PollData:
    def __init__(self, guild_id: int, msg_id: int) -> None:
        self.guild_id = guild_id
        self.msg_id = msg_id

        cur = db.cursor()
        cur.execute("""create table if not exists polls
(
    guild_id integer, 
    message_id integer,
    question text, 
    ans1 text, 
    ans2 text, 
    ans3 text, 
    ans4 text, 
    ans5 text,
    closed integer default 0,
    constraint polls_pk 
        primary key (guild_id, message_id)
);""")
        cur.execute('''create table if not exists polls_answers
(
    guild_id   integer,
    message_id integer,
    member_id  integer,
    choice     integer,
    constraint polls_answers_pk
        primary key (message_id, guild_id, member_id)
);''')

        cur.execute("SELECT guild_id, message_id, question, ans1, ans2, ans3, ans4, ans5, closed FROM polls WHERE "
                    "guild_id = ? AND message_id = ?", (guild_id, msg_id))

        data = cur.fetchone()
        if not data:
            self.ans1 = ''
            self.ans2 = ''
            self.ans3 = ''
            self.ans4 = ''
            self.ans5 = ''
            self.ans1_votes = []
            self.ans2_votes = []
            self.ans3_votes = []
            self.ans4_votes = []
            self.ans5_votes = []
            self.question = ''
        else:
            self.ans1 = data[3]
            self.ans2 = data[4]
            self.ans3 = data[5]
            self.ans4 = data[6]
            self.ans5 = data[7]
            self.question = data[2]
            self.closed = data[8] == 1

            cur.execute("SELECT member_id, choice FROM polls_answers WHERE guild_id = ? AND message_id = ?",
                        (guild_id, msg_id))
            for row in cur.fetchall():
                if row[1] == 1:
                    self.ans1_votes.append(row[0])
                elif row[1] == 2:
                    self.ans2_votes.append(row[0])
                elif row[1] == 3:
                    self.ans3_votes.append(row[0])
                elif row[1] == 4:
                    self.ans4_votes.append(row[0])
                elif row[1] == 5:
                    self.ans5_votes.append(row[0])

        cur.close()
        db.commit()

    def save(self):
        def insert_votes():
            for member_id in self.ans1_votes:
                cur.execute(
                    'select * from polls_answers where guild_id = ? and message_id = ? and member_id = ?',
                    (self.guild_id, self.msg_id, member_id))
                if not cur.fetchone():
                    cur.execute(
                        'insert into polls_answers (guild_id, message_id, member_id, choice) values (?, ?, ?, ?)',
                        (self.guild_id, self.msg_id, member_id, 1))

            for member_id in self.ans2_votes:
                cur.execute(
                    'select * from polls_answers where guild_id = ? and message_id = ? and member_id = ?',
                    (self.guild_id, self.msg_id, member_id))
                if not cur.fetchone():
                    cur.execute(
                        'insert into polls_answers (guild_id, message_id, member_id, choice) values (?, ?, ?, ?)',
                        (self.guild_id, self.msg_id, member_id, 2))

            for member_id in self.ans3_votes:
                cur.execute(
                    'select * from polls_answers where guild_id = ? and message_id = ? and member_id = ?',
                    (self.guild_id, self.msg_id, member_id))
                if not cur.fetchone():
                    cur.execute(
                        'insert into polls_answers (guild_id, message_id, member_id, choice) values (?, ?, ?, ?)',
                        (self.guild_id, self.msg_id, member_id, 3))

            for member_id in self.ans4_votes:
                cur.execute(
                    'select * from polls_answers where guild_id = ? and message_id = ? and member_id = ?',
                    (self.guild_id, self.msg_id, member_id))
                if not cur.fetchone():
                    cur.execute(
                        'insert into polls_answers (guild_id, message_id, member_id, choice) values (?, ?, ?, ?)',
                        (self.guild_id, self.msg_id, member_id, 4))

            for member_id in self.ans5_votes:
                cur.execute(
                    'select * from polls_answers where guild_id = ? and message_id = ? and member_id = ?',
                    (self.guild_id, self.msg_id, member_id))
                if not cur.fetchone():
                    cur.execute(
                        'insert into polls_answers (guild_id, message_id, member_id, choice) values (?, ?, ?, ?)',
                        (self.guild_id, self.msg_id, member_id, 5))

        cur = db.cursor()
        cur.execute('select guild_id, message_id from polls where guild_id = ? and message_id = ?',
                    (self.guild_id, self.msg_id))
        if cur.fetchone():
            cur.execute(
                'update polls '
                'set ans1 = ?, ans2 = ?, ans3 = ?, ans4 = ?, ans5 = ?, question = ?, closed = ? '
                'where guild_id = ? and message_id = ?',
                (self.ans1, self.ans2, self.ans3, self.ans4, self.ans5, self.question, 1 if self.closed else 0,
                 self.guild_id, self.msg_id))
            insert_votes()
        else:
            cur.execute(
                'insert into polls (guild_id, message_id, ans1, ans2, ans3, ans4, ans5, question, closed) '
                'values (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (self.guild_id, self.msg_id, self.ans1, self.ans2, self.ans3, self.ans4, self.ans5, self.question,
                 1 if self.closed else 0))
            insert_votes()

        cur.close()
        db.commit()

    def has_voted(self, member_id: int):
        return member_id in self.ans1_votes or member_id in self.ans2_votes or member_id in self.ans3_votes or member_id in self.ans4_votes or member_id in self.ans5_votes

    def set_question(self, question: str):
        self.question = question
        self.save()

    def set_answers(self, answers: list[str]):
        self.ans1 = answers[0]
        self.ans2 = answers[1]
        if self.answer_count >= 3:
            self.ans3 = answers[2]
        if self.answer_count >= 4:
            self.ans4 = answers[3]
        if self.answer_count >= 5:
            self.ans5 = answers[4]

        self.save()

    def add_vote(self, member_id: int, option: int) -> str:
        if self.has_voted(member_id):
            return "status:already_voted"

        if option < 1 or option > self.answer_count:
            return "status:invalid_option"

        if option == 1:
            self.ans1_votes.append(member_id)
            voted_opt = self.ans1
        if option == 2:
            self.ans2_votes.append(member_id)
            voted_opt = self.ans2
        if option == 3:
            self.ans3_votes.append(member_id)
            voted_opt = self.ans3
        if option == 4:
            self.ans4_votes.append(member_id)
            voted_opt = self.ans4
        if option == 5:
            self.ans5_votes.append(member_id)
            voted_opt = self.ans5

        self.save()
        return voted_opt

    question = ""

    @property
    def answer_count(self):
        answer_count = 2
        if self.ans3 != "":
            answer_count += 1
        if self.ans4 != "":
            answer_count += 1
        if self.ans5 != "":
            answer_count += 1
        return answer_count

    ans1 = ""
    ans2 = ""
    ans3 = ""
    ans4 = ""
    ans5 = ""

    ans1_votes = []
    ans2_votes = []
    ans3_votes = []
    ans4_votes = []
    ans5_votes = []

    closed = False
