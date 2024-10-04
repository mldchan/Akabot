from database import client


def get_per_user_setting(user_id: int, setting_name: str, default_value: str) -> str:
    res = client['UserSettings'].find_one({'UserID': user_id})
    return res[setting_name] if setting_name in res else default_value


def set_per_user_setting(user_id: int, setting_name: str, setting_value: str):
    client['UserSettings'].update_one({'UserID': user_id}, {'$set': {setting_name: setting_value}})


def unset_per_user_setting(user_id: int, setting_name: str):
    client['UserSettings'].update_one({'UserID': user_id}, {'$unset': {setting_name: 1}})
