import datetime

import discord
from bson import ObjectId

from database import client
from utils.generic import get_date_time_str, pretty_time_delta
from utils.languages import get_translation_for_key_localized as trl
from utils.settings import get_setting


async def add_warning(user: discord.Member, guild: discord.Guild, reason: str) -> ObjectId:
    id = db_add_warning(guild.id, user.id, reason)

    warning_should_dm = get_setting(guild.id, 'send_warning_message', 'true')
    if warning_should_dm == 'true':
        warning_message = get_setting(guild.id, 'warning_message', 'You have been warned in {guild} for {reason}.')

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
        if len(warnings) == action['Warnings']:  # only apply if the number of warnings matches, not if below
            if action['Action'] == 'kick':
                # try dm user
                try:
                    await user.send(
                        trl(user.id, guild.id, "warn_actions_auto_kick_dm").format(name=guild.name, warnings=action['Warnings']))
                except Exception:
                    pass
                await user.kick(
                    reason=trl(user.id, guild.id, "warn_actions_auto_kick_reason").format(warnings=action['Warnings']))
            elif action['Action'] == 'ban':
                # try dm user
                try:
                    await user.send(
                        trl(user.id, guild.id, "warn_actions_auto_ban_dm").format(name=guild.name, warnings=action['Warnings']))
                except Exception:
                    pass
                await user.ban(reason=trl(user.id, guild.id, "warn_actions_auto_ban_reason").format(warnings=action['Warnings']))
            elif action['Action'].startswith('timeout'):
                time = action['Action'].split(' ')[1]
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
                        trl(user.id, guild.id, "warn_actions_auto_timeout_dm").format(name=guild.name,
                                                                                      warnings=action['Warnings'],
                                                                                      time=pretty_time_delta(
                                                                                          total_seconds,
                                                                                          user_id=user.id,
                                                                                          server_id=guild.id)))
                except Exception:
                    pass

                await user.timeout_for(datetime.timedelta(seconds=total_seconds),
                                       reason=trl(user.id, guild.id, "warn_actions_auto_timeout_reason").format(
                                           warnings=action['Warnings']))

    return id


def db_add_warning(guild_id: int, user_id: int, reason: str) -> ObjectId:
    res = client['Warnings'].insert_one({'GuildID': guild_id, 'UserID': user_id, 'Reason': reason, 'Timestamp': get_date_time_str(guild_id)})
    return res.inserted_id


def db_get_warnings(guild_id: int, user_id: int) -> list[dict]:
    res = client['Warnings'].find({'GuildID': guild_id, 'UserID': user_id}).to_list()
    return res


def db_remove_warning(guild_id: int, warning_id: str):
    if not ObjectId.is_valid(warning_id):
        return

    client['Warnings'].delete_one({'GuildID': guild_id, '_id': ObjectId(warning_id)})


def db_add_warning_action(guild_id: int, action: str, warnings: int):
    client['WarningActions'].insert_one({'GuildID': guild_id, 'Action': action, 'Warnings': warnings})


def db_get_warning_actions(guild_id: int) -> list[dict]:
    res = client['WarningActions'].find({'GuildID': guild_id}).to_list()
    return res


def db_remove_warning_action(id: str):
    if not ObjectId.is_valid(id):
        return
    client['WarningActions'].delete_one({'_id': id})
