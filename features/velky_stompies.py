import discord


class VelkyStompies(discord.Cog):

    @discord.slash_command(name="stompies", description="Stompies")
    async def velky_stompies(self, ctx: discord.ApplicationContext):
        await ctx.respond("https://tenor.com/view/stompies-velky-cute-angwy-gif-13012534518393437613")
