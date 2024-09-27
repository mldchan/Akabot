
import discord

from utils.settings import get_setting


async def log_into_logs(server: discord.Guild, message: discord.Embed):
    log_id = await get_setting(server.id, 'logging_channel', '0')
    log_chan = server.get_channel(int(log_id))
    if log_chan is None:
        return

    if not log_chan.can_send():
        return

    await log_chan.send(embed=message)
