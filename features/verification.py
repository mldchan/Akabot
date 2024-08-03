import random

import discord
import discord.ext
import discord.ext.commands

import utils.english_words
import utils.logging_util
import utils.settings
from utils.logging_util import log_into_logs
from utils.languages import get_translation_for_key_localized as trl
from utils.analytics import analytics


async def give_verify_role(interaction: discord.Interaction | discord.ApplicationContext):
    # Bot permission check
    if not interaction.guild.me.guild_permissions.manage_roles:
        await interaction.response.send_message(
            trl(interaction.user.id, interaction.guild.id, "verification_role_no_permission"),
            ephemeral=True)

    # Get role from settings and check if it is set
    role_id = utils.settings.get_setting(interaction.guild.id, "verification_role", "-1")
    if role_id == "-1":
        await interaction.response.send_message(
            trl(interaction.user.id, interaction.guild.id, "verification_role_not_set"),
            ephemeral=True)
        return

    # Role existant check
    role = interaction.guild.get_role(int(role_id))
    if role is None:
        await interaction.response.send_message(
            trl(interaction.user.id, interaction.guild.id, "verification_role_invalid"), ephemeral=True)
        return

    # Role position check
    if role.position > interaction.guild.me.top_role.position:
        await interaction.response.send_message(
            trl(interaction.user.id, interaction.guild.id, "verification_role_no_permission"),
            ephemeral=True)
        return

    # Give out role
    await interaction.user.add_roles(role)


async def is_verified(interaction: discord.ApplicationContext) -> bool:
    # Get role from settings and check if it is set
    role_id = utils.settings.get_setting(interaction.guild.id, "verification_role", "-1")
    if role_id == "-1":
        return False

    # Role existant check
    role = interaction.guild.get_role(int(role_id))
    if role is None:
        return False

    return role in interaction.user.roles


class VerificationTextReverse(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=180)
        self.user_id = user_id

        # Random English word (to make it easier) and reverse it right away
        self.english_word = utils.english_words.get_random_english_word()[::-1]

    def message_content(self) -> str:
        # Message
        return trl(self.user_id, 0, "verification_reverse_word").format(word=self.english_word)

    @discord.ui.button(label="Answer", style=discord.ButtonStyle.primary)
    async def respond(self, btn: discord.Button, ctx: discord.ApplicationContext):
        # Respond with modal
        modal = VerificationTextReverseModal(word=self.english_word, user_id=self.user_id)
        await ctx.response.send_modal(modal)


class VerificationTextReverseModal(discord.ui.Modal):
    def __init__(self, word: str, user_id: int) -> None:
        super().__init__(title="Verification", timeout=180)
        self.word_right = word[::-1]
        self.user_id = user_id

        self.text_1 = discord.ui.InputText(label=trl(user_id, 0, "verification_form_reversed_word"), required=True,
                                           min_length=len(self.word_right),
                                           max_length=len(self.word_right))
        self.add_item(self.text_1)

    async def callback(self, interaction: discord.Interaction):
        # We assume the length is correct
        # Verify the English word
        if self.text_1.value != self.word_right:
            await interaction.response.send_message(trl(self.user_id, 0, "verification_form_word_incorrect"),
                                                    ephemeral=True)
            return

        await give_verify_role(interaction)
        await interaction.response.send_message(trl(self.user_id, 0, "verification_success"), ephemeral=True)


class VerificationEnglishWord(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=180)
        self.user_id = user_id

        self.length = random.randint(2, 8)

    def message_content(self) -> str:
        return trl(self.user_id, 0, "verification_english_word").format(self.length)

    @discord.ui.button(label="Answer", style=discord.ButtonStyle.primary)
    async def respond(self, btn: discord.Button, ctx: discord.ApplicationContext):
        # Respond with modal
        modal = VerificationEnglishWordModal(length=self.length, user_id=self.user_id)
        await ctx.response.send_modal(modal)


class VerificationEnglishWordModal(discord.ui.Modal):
    def __init__(self, length: int, user_id: int) -> None:
        super().__init__(title="Verification", timeout=180)
        self.length = length
        self.user_id = user_id

        self.text_1 = discord.ui.InputText(label=trl(user_id, 0, "verification_form_english_word"), required=True,
                                           min_length=self.length, max_length=self.length)
        self.add_item(self.text_1)

    async def callback(self, interaction: discord.Interaction):
        # We assume the length is correct
        # Verify the English word
        if not utils.english_words.verify_english_word(self.text_1.value):
            await interaction.response.send_message(trl(self.user_id, 0, "verification_form_not_english"),
                                                    ephemeral=True)
            return

        await give_verify_role(interaction)
        await interaction.response.send_message(trl(self.user_id, 0, "verification_success"), ephemeral=True)


class VerificationMath(discord.ui.View):

    def __init__(self, difficulty: str, user_id: int):
        super().__init__(timeout=180)
        self.user_id = user_id

        if difficulty == "easy":
            self.a = random.randint(0, 10)
            self.b = random.randint(0, 10)
        elif difficulty == "medium":
            self.a = random.randint(0, 100)
            self.b = random.randint(0, 100)
        elif difficulty == "hard":
            self.a = random.randint(-1000, 1000)
            self.b = random.randint(-1000, 1000)

        # Possible operators
        self.ops = ["+", "-", "*"]

        # Division operator if there's no remainder
        if self.b != 0 and self.a % self.b == 0:
            self.ops = self.ops.extend(["/"])

        # Random operator
        self.op = random.choice(self.ops)

        # Determine result
        if self.op == "+":
            self.result = self.a + self.b
        elif self.op == "-":
            self.result = self.a - self.b
        elif self.op == "*":
            self.result = self.a * self.b

    def message_content(self) -> str:
        # Create a message
        return trl(self.user_id, 0, "verification_math").format(a=self.a, b=self.b, o=self.op)

    @discord.ui.button(label="Answer", style=discord.ButtonStyle.primary)
    async def respond(self, btn: discord.Button, ctx: discord.ApplicationContext):
        # Respond with modal
        await ctx.response.send_modal(VerificationMathModal(result=self.result, user_id=self.user_id))


class VerificationMathModal(discord.ui.Modal):
    def __init__(self, result: int, user_id: int) -> None:
        super().__init__(timeout=180, title=trl(user_id, 0, "verification_form_title"))
        self.user_id = user_id
        self.right_result = str(result)
        self.text_1 = discord.ui.InputText(label=trl(user_id, 0, "verification_form_math"), required=True, min_length=1,
                                           max_length=4)
        self.add_item(self.text_1)

    async def callback(self, interaction: discord.Interaction):
        if self.text_1.value == self.right_result:
            await give_verify_role(interaction)
            await interaction.response.send_message(trl(self.user_id, 0, "verification_success"), ephemeral=True)
        else:
            await interaction.response.send_message(trl(self.user_id, 0, "verification_math_incorrect"), ephemeral=True)


class VerificationView(discord.ui.View):
    def __init__(self, custom_verify_label: str = "Verify"):
        super().__init__(timeout=None)

        button_1 = discord.ui.Button(label=custom_verify_label, custom_id="verify", style=discord.ButtonStyle.primary)
        button_1.callback = self.button_callback
        self.add_item(button_1)

    @analytics("\"Verify\" button click")
    async def button_callback(self, ctx: discord.ApplicationContext):

        if await is_verified(ctx):
            await ctx.respond("You're already verified.", ephemeral=True)
            return

        method = utils.settings.get_setting(ctx.guild.id, "verification_method", "none")

        if method == "none":
            # No verification method, give immediately role
            await give_verify_role(ctx)
            await ctx.respond("You have been verified successfully.", ephemeral=True)
        elif method == "easy_math":
            # Verify using a simple math problem
            simple_view = VerificationMath("easy", user_id=ctx.user.id)
            await ctx.respond(simple_view.message_content(), view=simple_view, ephemeral=True)
        elif method == "medium_math":
            # Verify using a medium math problem
            medium_view = VerificationMath("medium", ctx.user.id)
            await ctx.respond(medium_view.message_content(), view=medium_view, ephemeral=True)
        elif method == "hard_math":
            # Verify using hard math problem
            hard_view = VerificationMath("hard", ctx.user.id)
            await ctx.respond(hard_view.message_content(), view=hard_view, ephemeral=True)
        elif method == "english_word":
            # Verify using an English word of a desired length
            english_word = VerificationEnglishWord(user_id=ctx.user.id)
            await ctx.respond(english_word.message_content(), view=english_word, ephemeral=True)
        elif method == "reverse_string":
            # Verify using a reversed English word and make the user reverse it back
            word_reverse = VerificationTextReverse(user_id=ctx.user.id)
            await ctx.respond(word_reverse.message_content(), view=word_reverse, ephemeral=True)


class Verification(discord.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot
        super().__init__()

    verification_subcommand = discord.SlashCommandGroup(name="verification",
                                                        description="Verification related commands")

    @verification_subcommand.command(name="set_role", description="Set a role for the verification command")
    @discord.ext.commands.has_permissions(manage_roles=True)
    @discord.ext.commands.bot_has_permissions(manage_roles=True)
    @analytics("verification set_role")
    async def set_role(self, ctx: discord.ApplicationContext, role: discord.Role):
        # Bot permission check
        if not ctx.guild.me.guild_permissions.manage_roles:
            await ctx.respond(
                trl(ctx.user.id, ctx.guild.id, "verification_set_role_no_perms"),
                ephemeral=True)

        # Role position check
        if ctx.guild.me.top_role.position < role.position:
            await ctx.respond(trl(ctx.user.id, ctx.guild.id, "verification_set_role_no_perms"), ephemeral=True)
            return

        utils.settings.set_setting(ctx.guild.id, "verification_role", str(role.id))
        await ctx.respond(trl(ctx.user.id, ctx.guild.id, "verification_set_success"), ephemeral=True)

    @verification_subcommand.command(name="set_difficulty", description="Set the verification difficulty")
    @discord.commands.option(name="difficulty",
                             choices=["none", "easy math", "medium math", "hard math", "random english word",
                                      "reverse text"])
    @discord.ext.commands.has_permissions(manage_roles=True)
    @discord.ext.commands.bot_has_permissions(manage_roles=True)
    @analytics("verification set_difficulty")
    async def set_difficulty(self, ctx: discord.ApplicationContext, difficulty: str):
        # Store old difficulty
        old_difficulty = utils.settings.get_setting(ctx.guild.id, "verification_method", "none")

        # Select new difficulty
        if difficulty == "none":
            utils.settings.set_setting(ctx.guild.id, "verification_method", "none")
        elif difficulty == "easy math":
            utils.settings.set_setting(ctx.guild.id, "verification_method", "easy_math")
        elif difficulty == "medium math":
            utils.settings.set_setting(ctx.guild.id, "verification_method", "medium_math")
        elif difficulty == "hard math":
            utils.settings.set_setting(ctx.guild.id, "verification_method", "hard_math")
        elif difficulty == "random english word":
            utils.settings.set_setting(ctx.guild.id, "verification_method", "english_word")
        elif difficulty == "reverse text":
            utils.settings.set_setting(ctx.guild.id, "verification_method", "reverse_string")

        # Generate logging embed
        logging_embed = discord.Embed(title=trl(0, ctx.guild.id, "verification_set_difficulty_log_title"))
        logging_embed.add_field(name=trl(0, ctx.guild.id, "logging_user"), value=f"{ctx.user.mention}")
        logging_embed.add_field(name=trl(0, ctx.guild.id, "logging_difficulty"),
                                value=f"{old_difficulty} -> {difficulty}")

        # Send to logs
        await log_into_logs(ctx.guild, logging_embed)

        # Respond
        await ctx.respond(
            trl(ctx.user.id, ctx.guild.id, "verification_set_difficulty_response").format(difficulty=difficulty),
            ephemeral=True)

    @verification_subcommand.command(name="send_message", description="Send the verification message")
    @discord.ext.commands.has_permissions(manage_guild=True)
    @discord.ext.commands.bot_has_permissions(manage_guild=True)
    @analytics("verification send_message")
    async def send_message(self, ctx: discord.ApplicationContext,
                           custom_verify_message: str = "Click the verify button below to verify!",
                           custom_verify_label: str = "Verify"):
        # Get the role and verify it was set
        ver_role_id = utils.settings.get_setting(ctx.guild.id, "verification_role", "-1")
        if ver_role_id == "-1":
            await ctx.respond(trl(ctx.user.id, ctx.guild.id, "verification_send_message_verification_role_not_set"),
                              ephemeral=True)
            return

        # Role existing check
        ver_role = ctx.guild.get_role(int(ver_role_id))
        if ver_role is None:
            await ctx.respond(trl(ctx.user.id, ctx.guild.id, "verification_role_doesnt_exist"), ephemeral=True)
            return

        # Role permissions checks
        if ctx.guild.me.top_role.position < ver_role.position:
            await ctx.respond(trl(ctx.user.id, ctx.guild.id, "verification_role_position"), ephemeral=True)
            return

        # Channel permissions
        if not ctx.channel.can_send():
            await ctx.respond(trl(ctx.user.id, ctx.guild.id, "verification_channel_send"), ephemeral=True)
            return

        # Create the view
        view = VerificationView(custom_verify_label=custom_verify_label)

        # Send the message
        await ctx.channel.send(content=custom_verify_message, view=view)

        # Respond to user that it was successfull
        await ctx.respond(trl(ctx.user.id, ctx.guild.id, "verification_send_success"), ephemeral=True)
