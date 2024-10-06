from pymongo import MongoClient

from utils.config import get_key

name = get_key("DB_Username", "")
password = get_key("DB_Password", "")
host = get_key("DB_Host", "localhost")
port = get_key("DB_Port", "27017")
db = get_key("DB_Database", "akabot")

client = MongoClient(f'mongodb://{name}:{password}@{host}:{port}/', 27017)[db]
