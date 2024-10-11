from database import client


def get_setting(server_id: int, key: str, default):
    res = client['ServerSettings'].find_one({'GuildID': str(server_id)})
    if key not in res:
        client['ServerSettings'].update_one({'GuildID': str(server_id)}, {'$set': {key: default}})

    return res[key] if res and key in res else default


def set_setting(server_id: int, key: str, value) -> None:
    if client['ServerSettings'].count_documents({'GuildID': str(server_id)}) == 0:
        client['ServerSettings'].insert_one({'GuildID': str(server_id)})

    if value is not None:
        client['ServerSettings'].update_one({'GuildID': str(server_id)}, {'$set': {key: value}})
    else:
        client['ServerSettings'].update_one({'GuildID': str(server_id)}, {'$unset': {key: 1}})
