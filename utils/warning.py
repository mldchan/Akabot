import datetime
import discord
from database import conn
from utils.generic import get_date_time_str, pretty_time_delta

async def add_warning(user: discord.Member, guild: discord.Guild, reason: str) -> int:
    id = db_add_warning(guild.id, user.id, reason)

    # try dm user
    try:
        await user.send(f'You have been warned in {guild.name} for {reason}.')
    except Exception:
        pass

    warnings = db_get_warnings(guild.id, user.id)
    actions = db_get_warning_actions(guild.id)

    if not actions:
        return id
    
    for action in actions:
        if len(warnings) == action[2]: # only apply if the number of warnings matches, not if below
            if action[1] == 'kick':
                # try dm user
                try:
                    await user.send(f'You have been kicked from {guild.name} for reaching {action[2]} warnings.')
                except Exception:
                    pass
                await user.kick(reason=f"Kicked for reaching {action[2]} warnings.")
            elif action[1] == 'ban':
                # try dm user
                try:
                    await user.send(f'You have been banned from {guild.name} for reaching {action[2]} warnings.')
                except Exception:
                    pass
                await user.ban(reason=f"Banned for reaching {action[2]} warnings.")
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
                    await user.send(f'You have been timed out from {guild.name} for reaching {action[2]} warnings for {pretty_time_delta(total_seconds)}.')
                except Exception:
                    pass

                await user.timeout_for(datetime.timedelta(seconds=total_seconds), reason=f"Timed out for reaching {action[2]} warnings.")

    return id

def db_add_warning(guild_id: int, user_id: int, reason: str) -> int:
    cur = conn.cursor()
    cur.execute('insert into warnings (guild_id, user_id, reason, timestamp) values (?, ?, ?, ?)',
                (guild_id, user_id, reason, get_date_time_str()))
    warning_id = cur.lastrowid
    cur.close()
    conn.commit()
    return warning_id

def db_get_warnings(guild_id: int, user_id: int):
    cur = conn.cursor()
    cur.execute('select id, reason, timestamp from warnings where guild_id = ? and user_id = ?', (guild_id, user_id))
    warnings = cur.fetchall()
    cur.close()
    return warnings

def db_remove_warning(guild_id: int, warning_id: int):
    cur = conn.cursor()
    cur.execute('delete from warnings where guild_id = ? and id = ?', (guild_id, warning_id))
    cur.close()
    conn.commit()

def db_add_warning_action(guild_id: int, action: str, warnings: int):
    # Add an action to be taken on a user with a certain number of warnings
    cur = conn.cursor()
    cur.execute('insert into warnings_actions (guild_id, action, warnings) values (?, ?, ?)',
                (guild_id, action, warnings))
    cur.close()
    conn.commit()

def db_get_warning_actions(guild_id: int):
    cur = conn.cursor()
    cur.execute('select id, action, warnings from warnings_actions where guild_id = ?', (guild_id,))
    actions = cur.fetchall()
    cur.close()
    return actions

def db_remove_warning_action(id: int):
    cur = conn.cursor()
    cur.execute('delete from warnings_actions where id = ?', (id,))
    cur.close()
    conn.commit()
