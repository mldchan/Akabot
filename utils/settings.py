import pymongo
import bson

def get_setting(db: pymongo.MongoClient, server_id: int, key: str, default: str) -> str | None:
    femboybot_db = db.get_database('FemboyBot')
    settings_coll = femboybot_db.get_collection('Settings')
    settings_serv = settings_coll.find_one({ 'server_id': server_id })
    if settings_serv is None:
        insert_result = settings_coll.insert_one({ 'server_id': server_id, 'settings': {key: default} })
        settings_serv = settings_coll.find_one({ '_id': bson.ObjectId(insert_result.inserted_id) })

    print('debug', settings_serv)

    return settings_serv['settings'][key]
