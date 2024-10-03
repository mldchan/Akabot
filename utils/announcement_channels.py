from database import client


def db_add_announcement_channel(guild_id: int, channel_id: int):
    data = client['AnnouncementChannels'].find_one({'GuildID': {'$eq': guild_id}, 'ChannelID': {'$eq': channel_id}})
    if not data:
        client['AnnouncementChannels'].insert_one({'GuildID': guild_id, 'ChannelID': channel_id})


def db_remove_announcement_channel(guild_id: int, channel_id: int):
    data = client['AnnouncementChannels'].find_one({'GuildID': {'$eq': guild_id}, 'ChannelID': {'$eq': channel_id}})
    if data:
        client['AnnouncementChannels'].delete_one({'GuildID': {'$eq': guild_id}, 'ChannelID': {'$eq': channel_id}})


def db_is_subscribed_to_announcements(guild_id: int, channel_id: int):
    data = client['AnnouncementChannels'].find_one({'GuildID': {'$eq': guild_id}, 'ChannelID': {'$eq': channel_id}})
    return data is not None


def db_get_announcement_channels(guild_id: int):
    data = client['AnnouncementChannels'].find({'GuildID': {'$eq': guild_id}}).to_list()
    return [(i['GuildID'], i['ChannelID']) for i in data]


def db_get_all_announcement_channels():
    data = client['AnnouncementChannels'].find().to_list()
    return [(i['GuildID'], i['ChannelID']) for i in data]
