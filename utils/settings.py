import pymongo
import bson

def get_setting(db: pymongo.MongoClient, server_id: int, key: str, default: str) -> str | None:
    femboybot_db = db.get_database('FemboyBot')
    settings_coll = femboybot_db.get_collection('Settings')
    settings_serv = settings_coll.find_one({ 'server_id': server_id })
    if settings_serv is None:
        insert_result = settings_coll.insert_one({ 'server_id': server_id, 'settings': {key: default} })
        settings_serv = settings_coll.find_one({ '_id': bson.ObjectId(insert_result.inserted_id) })

    if key not in settings_serv['settings']:
        settings_coll.update_one({ 'server_id': server_id }, { '$set': { f'settings.{key}': default }})
        settings_serv = settings_coll.find_one({ 'server_id': server_id })

    return settings_serv['settings'][key]

def set_setting(db: pymongo.MongoClient, server_id: int, key: str, value: str) -> None:
    femboybot_db = db.get_database('FemboyBot')
    settings_coll = femboybot_db.get_collection('Settings')
    settings_coll.update_one({ 'server_id': server_id }, { '$set': { f'settings.{key}': value }})
