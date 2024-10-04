from database import client


def get_setting(server_id: int, key: str, default: str) -> str:
    res = client['ServerSettings'].find_one({'ServerID': server_id})
    return res[key] or default


def set_setting(server_id: int, key: str, value: str) -> None:
    client['ServerSettings'].update_one({'ServerID': server_id}, {'$set': {key: value}})
