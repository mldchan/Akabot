import discord


class VelkyStompies(discord.Cog):

    @discord.slash_command(name="stompies", description="Stompies", guild_ids=[1234573274504237087])
    async def velky_stompies(self, ctx: discord.ApplicationContext):
        await ctx.response.send_message("https://media.discordapp.net/attachments/1245011636427948032/1246739873138999316/RiLSorG.gif?ex=665d7c7d&is=665c2afd&hm=ceda1940a25a4d863d81ed9c118fb488b7271d3e8a774cb309c7a8faa9e86d25&=&width=815&height=459")
