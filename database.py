import os

import aiosqlite

if not os.path.exists('data'):
    os.mkdir('data')

async def get_conn():
    return await aiosqlite.connect('data/femboybot.db')
