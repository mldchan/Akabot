import datetime

import discord

from database import get_conn
from utils.generic import get_date_time_str, pretty_time_delta
from utils.languages import get_translation_for_key_localized as trl
from utils.settings import get_setting


async def add_warning(user: discord.Member, guild: discord.Guild, reason: str) -> int:
    id = db_add_warning(guild.id, user.id, reason)

    warning_should_dm = await get_setting(guild.id, 'send_warning_message', 'true')
    if warning_should_dm == 'true':
        warning_message = await get_setting(guild.id, 'warning_message', 'You have been warned in {guild} for {reason}.')

        warning_message = warning_message.replace('{name}', user.display_name)
        warning_message = warning_message.replace('{guild}', guild.name)
        warning_message = warning_message.replace('{reason}', reason)
        warning_message = warning_message.replace('{warnings}', str(len(db_get_warnings(guild.id, user.id))))

        # try dm user
        try:
            await user.send(warning_message)
        except Exception:
            pass

    warnings = db_get_warnings(guild.id, user.id)
    actions = db_get_warning_actions(guild.id)

    if not actions:
        return id

    for action in actions:
        if len(warnings) == action[2]:  # only apply if the number of warnings matches, not if below
            if action[1] == 'kick':
                # try dm user
                try:
                    await user.send(
                        await trl(user.id, guild.id, "warn_actions_auto_kick_dm").format(name=guild.name, warnings=action[2]))
                except Exception:
                    pass
                await user.kick(
                    reason=await trl(user.id, guild.id, "warn_actions_auto_kick_reason").format(warnings=action[2]))
            elif action[1] == 'ban':
                # try dm user
                try:
                    await user.send(
                        await trl(user.id, guild.id, "warn_actions_auto_ban_dm").format(name=guild.name, warnings=action[2]))
                except Exception:
                    pass
                await user.ban(reason=await trl(user.id, guild.id, "warn_actions_auto_ban_reason").format(warnings=action[2]))
            elif action[1].startswith('timeout'):
                time = action[1].split(' ')[1]
                total_seconds = 0
                if time == '12h':
                    total_seconds = 43200
                elif time == '1d':
                    total_seconds = 86400
                elif time == '7d':
                    total_seconds = 604800
                elif time == '28d':
                    total_seconds = 2419200

                # try dm
                try:
                    await user.send(
                        await trl(user.id, guild.id, "warn_actions_auto_timeout_dm").format(name=guild.name,
                                                                                      warnings=action[2],
                                                                                      time=await pretty_time_delta(
                                                                                          total_seconds,
                                                                                          user_id=user.id,
                                                                                          server_id=guild.id)))
                except Exception:
                    pass

                await user.timeout_for(datetime.timedelta(seconds=total_seconds),
                                       reason=await trl(user.id, guild.id, "warn_actions_auto_timeout_reason").format(
                                           warnings=action[2]))

    return id


async def db_add_warning(guild_id: int, user_id: int, reason: str) -> int:
    db = await get_conn()
    cur = await db.execute('insert into warnings (guild_id, user_id, reason, timestamp) values (?, ?, ?, ?)',
                (guild_id, user_id, reason, get_date_time_str(guild_id)))
    warning_id = cur.lastrowid
    await db.commit()
    await db.close()
    return warning_id


async def db_get_warnings(guild_id: int, user_id: int):
    db = await get_conn()
    cur = await db.execute('select id, reason, timestamp from warnings where guild_id = ? and user_id = ?', (guild_id, user_id))
    warnings = await cur.fetchall()
    await db.close()
    return warnings


async def db_remove_warning(guild_id: int, warning_id: int):
    db = await get_conn()
    await db.execute('delete from warnings where guild_id = ? and id = ?', (guild_id, warning_id))
    await db.commit()
    await db.close()


async def db_add_warning_action(guild_id: int, action: str, warnings: int):
    # Add an action to be taken on a user with a certain number of warnings
    db = await get_conn()
    await db.execute('insert into warnings_actions (guild_id, action, warnings) values (?, ?, ?)',
                (guild_id, action, warnings))
    await db.commit()
    await db.close()


async def db_get_warning_actions(guild_id: int):
    db = await get_conn()
    cur = await db.execute('select id, action, warnings from warnings_actions where guild_id = ?', (guild_id,))
    actions = await cur.fetchall()
    await db.close()
    return actions


async def db_remove_warning_action(id: int):
    db = await get_conn()
    await db.execute('delete from warnings_actions where id = ?', (id,))
    await db.commit()
    await db.close()
