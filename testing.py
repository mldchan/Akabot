import pymongo
import json
import bson
from datetime import datetime

with open('config.json', 'r') as f:
    data = json.load(f)

client = pymongo.MongoClient(data['conn_string'])

tokens_coll = client.get_database('FemboyBot').get_collection('WebTokens')

unix_timestamp = int(round((datetime.now() - datetime(1970, 1, 1)).total_seconds(), 0))

for token in tokens_coll.find():
    print(token['expires'])
    print(unix_timestamp)
    
tokens_coll.delete_many({'expires': {'$lt': unix_timestamp}}) # WAIT THIS IS SO FUCKIGN COOL!!!
