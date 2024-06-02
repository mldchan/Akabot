import discord

import discord.ext
import discord.ext.commands
from discord.ui.input_text import InputText

import utils.settings
import random

import utils.english_words

async def give_verify_role(interaction: discord.Interaction):
    # Bot permission check
    if not interaction.guild.me.guild_permissions.manage_roles:
        await interaction.response.send_message("I can't give you the role because I don't have permissions to do so. Contact administrators with the following information: The bot doesn't have the following permissions: Manage Roles", ephemeral=True)

    # Get role from settings and check if it is set
    role_id = utils.settings.get_setting(interaction.guild.id, "verification_role", "-1")
    if role_id == "-1":
        await interaction.response.send_message("The role is not set. Contact administrators to fix this.", ephemeral=True)
        return
    
    # Role existant check
    role = interaction.guild.get_role(int(role_id))
    if role is None:
        await interaction.response.send_message("The verification role set is now invalid. Contact administrators to fix this.", ephemeral=True)
        return
    
    # Role position check
    if role.position > interaction.guild.me.top_role.position:
        await interaction.response.send_message("I can't give you the role because I don't have permissions to do so. Contact administrators with the following information: The role is higher than the bot's role, making the bot unable to assign the role.", ephemeral=True)
        return
    
    # Give out role
    await interaction.user.add_roles(role)
    
async def is_verified(interaction: discord.Interaction) -> bool:
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
    def __init__(self):
        super().__init__(timeout=180)

        # Random English word (to make it easier) and reverse it right away
        self.english_word = utils.english_words.get_random_english_word()[::-1]


    def message_content(self) -> str:
        # Message
        return f"To get verified, reverse the following word: ***{self.english_word}***."

    @discord.ui.button(label="Answer", style=discord.ButtonStyle.primary)
    async def respond(self, btn: discord.Button, ctx: discord.ApplicationContext):
        # Respond with modal
        modal = VerificationTextReverseModal(word=self.english_word)
        await ctx.response.send_modal(modal)


class VerificationTextReverseModal(discord.ui.Modal):
    def __init__(self, word: str) -> None:
        super().__init__(title="Verification", timeout=180)
        self.word_right = word[::-1]

        self.text_1 = discord.ui.InputText(label=f"Reversed word", required=True, min_length=len(self.word_right), max_length=len(self.word_right))
        self.add_item(self.text_1)

    async def callback(self, interaction: discord.Interaction):
        # We assume the length is correct
        # Verify the English word
        if self.text_1.value != self.word_right:
            await interaction.response.send_message("The word you've entered is incorrect", ephemeral=True)
            return
        
        await give_verify_role(interaction)
        await interaction.response.send_message("Verified successfully!", ephemeral=True)
    
class VerificationEnglishWord(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)

        self.length = random.randint(2, 8)


    def message_content(self) -> str:
        return f"To get verified, respond with any English word that is {self.length} letters long."

    @discord.ui.button(label="Answer", style=discord.ButtonStyle.primary)
    async def respond(self, btn: discord.Button, ctx: discord.ApplicationContext):
        # Respond with modal
        modal = VerificationEnglishWordModal(length=self.length)
        await ctx.response.send_modal(modal)


class VerificationEnglishWordModal(discord.ui.Modal):
    def __init__(self, length: int) -> None:
        super().__init__(title="Verification", timeout=180)
        self.length = length

        self.text_1 = discord.ui.InputText(label=f"Type any English word with {length} letters", required=True, min_length=self.length, max_length=self.length)
        self.add_item(self.text_1)

    async def callback(self, interaction: discord.Interaction):
        # We assume the length is correct
        # Verify the English word
        if not utils.english_words.verify_english_word(self.text_1.value):
            await interaction.response.send_message("The word you've entered is not an English word.", ephemeral=True)
            return
        
        await give_verify_role(interaction)
        await interaction.response.send_message("Verified successfully!", ephemeral=True)


class VerificationMath(discord.ui.View):
    
    def __init__(self, difficulty: str):
        super().__init__(timeout=180)
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
        if self.a % self.b == 0:
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
        return f"To get verified, you'll need to pass a simple verification procedure:\n\n***{self.a} {self.op} {self.b} = ?***"
    
    @discord.ui.button(label="Answer", style=discord.ButtonStyle.primary)
    async def respond(self, btn: discord.Button, ctx: discord.ApplicationContext):
        # Respond with modal
        await ctx.response.send_modal(VerificationMathModal(result=self.result))


class VerificationMathModal(discord.ui.Modal):
    def __init__(self, result: int) -> None:
        super().__init__(timeout=180, title="Verification")
        self.right_result = str(result)
        self.text_1 = discord.ui.InputText(label="What is the result of the math problem?", required=True, min_length=1, max_length=4)
        self.add_item(self.text_1)

    async def callback(self, interaction: discord.Interaction):
        if self.text_1.value == self.right_result:
            await give_verify_role(interaction)
            await interaction.response.send_message("You have been verified successfully!", ephemeral=True)
        else:
            await interaction.response.send_message("That answer was wrong. Please try again.", ephemeral=True)

class VerificationView(discord.ui.View):
    def __init__(self, custom_verify_label: str = "Verify"):
        super().__init__(timeout=None)

        button_1 = discord.ui.Button(label=custom_verify_label, custom_id="verify", style=discord.ButtonStyle.primary)
        button_1.callback = self.button_callback
        self.add_item(button_1)

    async def button_callback(button: discord.Button, ctx: discord.ApplicationContext):

        if await is_verified(ctx):
            await ctx.response.send_message("You're already verified.", ephemeral=True)
            return

        method = utils.settings.get_setting(ctx.guild.id, "verification_method", "none")

        if method == "none":
            # No verification method, give immediately role
            await give_verify_role(ctx)
            await ctx.response.send_message("You have been verified successfully.", ephemeral=True)
        elif method == "easy_math":
            # Verify using a simple math problem
            simple_view = VerificationMath("easy")
            await ctx.response.send_message(simple_view.message_content(), view=simple_view, ephemeral=True)
        elif method == "medium_math":
            # Verify using a medium math problem
            medium_view = VerificationMath("medium")
            await ctx.response.send_message(medium_view.message_content(), view=medium_view, ephemeral=True)
        elif method == "hard_math":
            # Verify using hard math problem
            hard_view = VerificationMath("hard")
            await ctx.response.send_message(hard_view.message_content(), view=hard_view, ephemeral=True)
        elif method == "english_word":
            # Verify using an English word of a desired length
            english_word = VerificationEnglishWord()
            await ctx.response.send_message(english_word.message_content(), view=english_word, ephemeral=True)
        elif method == "reverse_string":
            # Verify using a reversed English word and make the user reverse it back
            word_reverse = VerificationTextReverse()
            await ctx.response.send_message(word_reverse.message_content(), view=word_reverse, ephemeral=True)


class Verification(discord.Cog):
    def __init__(self, bot: discord.Bot) -> None:
        self.bot = bot
        super().__init__()

    verification_subcommand = discord.SlashCommandGroup(name="verification", description="Verification related commands")

    @verification_subcommand.command(name="set_role", description="Set a role for the verification command")
    @discord.ext.commands.has_permissions(manage_roles=True)
    @discord.ext.commands.bot_has_permissions(manage_roles=True)
    async def set_role(self, ctx: discord.ApplicationContext, role: discord.Role):
        # Bot permission check
        if not ctx.guild.me.guild_permissions.manage_roles:
            await ctx.response.send_message("I can't give you the role because I don't have permissions to do so. Contact administrators with the following information: The bot doesn't have the following permissions: Manage Roles", ephemeral=True)

        # Role position check
        if ctx.guild.me.top_role.position < role.position:
            await ctx.response.send_message(f"The {role.name} has to be under the bot's role for this to work", ephemeral=True)
            return
        
        utils.settings.set_setting(ctx.guild.id, "verification_role", role.id)
        await ctx.response.send_message("Set verification role successfully.", ephemeral=True)

    @verification_subcommand.command(name="set_difficulty", description="Set the verification difficulty")
    @discord.commands.option(name="difficulty", choices=["none", "easy math", "medium math", "hard math", "random english word", "reverse text"])
    @discord.ext.commands.has_permissions(manage_roles=True)
    @discord.ext.commands.bot_has_permissions(manage_roles=True)
    async def set_difficulty(self, ctx: discord.ApplicationContext, difficulty: str):
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
        
        # TODO: rest of options
        await ctx.response.send_message(f"Verification difficulty was set to {difficulty}.", ephemeral=True)

    @verification_subcommand.command(name="send_message", description="Send the verification message")
    @discord.ext.commands.has_permissions(manage_guild=True)
    @discord.ext.commands.bot_has_permissions(manage_guild=True)
    async def send_message(self, ctx: discord.ApplicationContext, custom_verify_message: str = "Click the verify button below to verify!", custom_verify_label: str = "Verify"):
        # Get the role and verify it was set
        ver_role_id = utils.settings.get_setting(ctx.guild.id, "verification_role", "-1")
        if ver_role_id == "-1":
            await ctx.response.send_message("The verification role is not set.", ephemeral=True)
            return
        
        # Role existing check
        ver_role = ctx.guild.get_role(int(ver_role_id))
        if ver_role is None:
            await ctx.response.send_message("The verification role set is invalid.", ephemeral=True)
            return
        
        # Role permissions checks
        if ctx.guild.me.top_role.position < ver_role.position:
            await ctx.response.send_message("The verification role has to be under the bot's role.", ephemeral=True)
            return
        
        # Channel permissions
        if not ctx.channel.can_send():
            await ctx.response.send_message("I have no permission to send messages in this channel.", ephemeral=True)
            return
        
        # Create the view
        view = VerificationView(custom_verify_label=custom_verify_label)
        
        # Send the message
        await ctx.channel.send(content=custom_verify_message, view=view)
        
        # Respond to user that it was successfull
        await ctx.response.send_message("Sent message successfully", ephemeral=True)
