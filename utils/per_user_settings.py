from database import client


def get_per_user_setting(user_id: int, setting_name: str, default_value) -> str:
    res = client['UserSettings'].find_one({'UserID': str(user_id)})
    return res[setting_name] if res and setting_name in res else default_value


def set_per_user_setting(user_id: int, setting_name: str, setting_value):
    if setting_name == "_id" or setting_name == "UserID":
        raise Exception('Invalid setting name')

    if client['UserSettings'].count_documents({'UserID': str(user_id)}) == 0:
        client['UserSettings'].insert_one({'UserID': str(user_id)})

    if setting_value is not None:
        client['UserSettings'].update_one({'UserID': str(user_id)}, {'$set': {setting_name: setting_value}})
    else:
        client['UserSettings'].update_one({'UserID': str(user_id)}, {'$unset': {setting_name: 1}})
