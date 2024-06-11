
import logging

import discord

from utils.settings import get_setting


async def log_into_logs(server: discord.Guild, message: discord.Embed):
    log_id = get_setting(server.id, 'logging_channel', '0')
    log_chan = server.get_channel(int(log_id))
    if log_chan is None:
        return

    logger = logging.getLogger("Akatsuki")
    logger.debug(f"Logs on {server.name} to {log_chan.name}: embed: {message.title}")
    logger.debug(message.description)
    for i in message.fields:
        logger.debug(f"Field: {i.name}: {i.value}")

    if not log_chan.can_send():
        logger.warning("Tried to send to logs but no permission!")
        return

    await log_chan.send(embed=message)
    logger.debug("Log was sent successfully!")
