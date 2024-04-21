import os
import sqlite3

if not os.path.exists('data'):
    os.mkdir('data')

conn = sqlite3.connect('data/femboybot.db')
