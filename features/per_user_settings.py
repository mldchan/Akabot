import discord

from utils.per_user_settings import set_per_user_setting


class PerUserSettings(discord.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

    user_settings_group = discord.SlashCommandGroup(name='user_settings', description='Per user settings')

    @user_settings_group.command(name='chat_streaks_alerts', description='Enable or disable chat streaks alerts')
    @discord.option(name='state', description='How notifications should be sent',
                    choices=['enabled', 'only when lost', 'off'])
    async def chat_streaks_alerts(self, ctx: discord.ApplicationContext, state: str):
        set_per_user_setting(ctx.user.id, 'chat_streaks_alerts', state)
        await ctx.respond(f'Chat streaks alerts are now {state}.', ephemeral=True)
