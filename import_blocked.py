import csv
import sqlite3

db = sqlite3.connect('../data2/femboybot.db')

cur = db.cursor()

with open('servers.csv', 'r', encoding='utf8') as f:
    reader = csv.reader(f, delimiter=';')
    for row in reader:
        cur.execute('INSERT INTO blocked_servers (id, reason) VALUES (?, ?)', (row[0], row[1]))

with open('users.csv', 'r', encoding='utf8') as f:
    reader = csv.reader(f, delimiter=';')
    for row in reader:
        cur.execute('INSERT INTO blocked_users (id, reason) VALUES (?, ?)', (row[0], row[1]))

cur.close()
db.commit()
