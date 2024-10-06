import datetime
import os
import sqlite3

from database import client


def update():
    if os.path.exists("data/converted.flag"):
        print('[DB Conversion] Conversion already done, skipping...')
        return

    conn = sqlite3.connect("data/femboybot.db")
    cur = conn.cursor()

    # Analytics

    cur.execute('select command, run_count from analytics')
    for i in cur.fetchall():
        client['Analytics'].update_one({'Command': i[0]}, {'$set': {'RunCount': i[1]}}, upsert=True)

    # Automod Actions

    cur.execute('select id, guild_id, rule_id, rule_name, action, additional from automod_actions')
    for i in cur.fetchall():
        client['AutomodActions'].update_one({'GuildID': str(i[1]), 'RuleID': i[2]}, {'$set': {'RuleName': i[3], 'Action': i[4], 'Additional': i[5]}}, upsert=True)

    # Chat Revive

    cur.execute('select guild_id, channel_id, role_id, revival_time, last_message, revived from chat_revive')
    for i in cur.fetchall():
        client['ChatRevive'].update_one({'GuildID': str(i[0]), 'ChannelID': str(i[1])},
                                        {'$set': {'RoleID': i[2], 'RevivalTime': i[3], 'LastMessage': datetime.datetime.now(datetime.UTC), 'Revived': i[5]}}, upsert=True)

    # Chat Summary

    cur.execute('select guild_id, channel_id, enabled, messages from chat_summary')
    for i in cur.fetchall():
        cur.execute('select guild_id, channel_id, member_id, messages from chat_summary_members where guild_id = ? and channel_id = ?', (i[0], i[1]))
        members = cur.fetchall()

        final_dict = {
            'Enabled': i[2],
            'MessageCount': i[3]
        }

        for j in members:
            final_dict[f'Messages.{str(j[2])}'] = j[3]

        client['ChatSummary'].update_one({
            'GuildID': str(i[0]),
            'ChannelID': str(i[1])
        }, {
            '$set': final_dict
        }, upsert=True)

    # Giveaways

    cur.execute('select id, channel_id, message_id, item, end_date, winner_count from giveaways')
    for i in cur.fetchall():
        cur.execute('select id, giveaway_id, user_id from giveaway_participants where giveaway_id = ?', (i[0],))
        participants = cur.fetchall()

        client['Giveaways'].insert_one({
            'ChannelID': str(i[1]),
            'MessageID': str(i[2]),
            'Item': i[3],
            'EndDate': i[4],
            'Winners': int(i[5]),
            'Participants': [{str(j[2]) for j in participants}]
        })

    # Leveling

    cur.execute('select guild_id, user_id, xp from leveling')
    for i in cur.fetchall():
        client['Leveling'].update_one({'GuildID': str(i[0]), 'UserID': str(i[1])}, {'$set': {'XP': int(i[2])}}, upsert=True)

    # Leveling: Multipliers

    cur.execute('select guild_id, name, multiplier, start_date, end_date from leveling_multiplier')
    for i in cur.fetchall():
        client['LevelingMultiplier'].update_one({
            'GuildID': str(i[0])
        }, {
            '$set': {
                'Name': i[1],
                'Multiplier': int(i[2]),
                'StartDate': i[3],
                'EndDate': i[4]
            }
        }, upsert=True)

    # Moderator Roles

    cur.execute('select guild_id, role_id from moderator_roles')
    for i in cur.fetchall():
        client['ModeratorRoles'].insert_one({'GuildID': str(i[0]), 'RoleID': str(i[1])})

    # Per User Settings
    cur.execute('select user_id from per_user_settings')
    for i in cur.fetchall():
        cur.execute('select id, user_id, setting_name, setting_value from per_user_settings where user_id = ?', (i[0],))
        settings = cur.fetchall()

        dict_settings = {}
        for j in settings:
            dict_settings[j[2]] = j[3]

        client['UserSettings'].update_one({'UserID': str(i[0])}, {'$set': dict_settings}, upsert=True)

    # Roles on Join

    cur.execute('select id, guild_id, role_id from roles_on_join')
    for i in cur.fetchall():
        client['RolesOnJoin'].insert_one({'GuildID': str(i[1]), 'RoleID': str(i[2])})

    # Server Settings

    cur.execute('select guild_id from settings')
    for i in cur.fetchall():
        cur.execute('select key, value from settings where guild_id = ?', (i[0],))

        dict_settings = {}
        for j in cur.fetchall():
            dict_settings[j[0]] = j[1]

        client['ServerSettings'].update_one({
            'GuildID': str(i[0])
        }, {
            '$set': dict_settings
        }, upsert=True)

    # Suggestion Channels

    cur.execute('select id, channel_id from suggestion_channels')
    for i in cur.fetchall():
        client['SuggestionChannels'].insert_one({'GuildID': str(i[0]), 'ChannelID': str(i[1])})

    # Temporary VC's

    cur.execute('select id, channel_id, guild_id from temporary_vc_creator_channels')
    for i in cur.fetchall():
        client['TemporaryVCCreators'].update_one({'GuildID': str(i[2]), 'ChannelID': str(i[1])}, {'$set': {}}, upsert=True)

    # Tickets

    cur.execute('select id, guild_id, ticket_channel_id, user_id, mtime, atime from tickets')
    for i in cur.fetchall():
        client['TicketChannels'].update_one({
            'GuildID': str(i[1]),
            'TicketChannelID': str(i[2])
        }, {
            '$set': {
                'UserID': str(i[3]),
                'MTime': datetime.datetime.fromisoformat(i[4]),
                'ATime': datetime.datetime.fromisoformat(i[5]) if i[5] != "None" else "None"
            }
        }, upsert=True)

    # Warnings

    cur.execute('select id, guild_id, user_id, reason, timestamp from warnings')
    for i in cur.fetchall():
        client['Warnings'].insert_one({
            'GuildID': str(i[1]),
            'UserID': str(i[2]),
            'Reason': i[3],
            'Timestamp': i[4]
        })

    # Warnings Actions

    cur.execute('select id, guild_id, warnings, action from warnings_actions')
    for i in cur.fetchall():
        client['WarningActions'].insert_one({
            'GuildID': str(i[1]),
            'Warnings': int(i[2]),
            'Action': i[3]
        })

    # Close and rename

    cur.close()
    conn.close()

    with open("data/converted.flag", "w") as f:
        f.write("")
