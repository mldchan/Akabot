
from database import get_conn


async def db_init():
    db = await get_conn()
    await db.execute("""create table if not exists settings
(
    guild_id integer,
    key      text,
    value    text,
    constraint settings_pk
        primary key (guild_id, key)
);""")
    await db.commit()
    await db.close()


async def db_get_key(guild_id: int, key: str):
    await db_init()
    db = await get_conn()
    cur = await db.execute(
        "SELECT value FROM settings WHERE guild_id = ? AND key = ?", (guild_id, key))
    result = await cur.fetchone()
    await db.close()
    return result[0] if result else None


async def db_set_key(guild_id: int, key: str, value: str):
    await db_init()
    db = await get_conn()
    cur = await db.execute(
        "select * from settings where guild_id = ? and key = ?", (guild_id, key))
    if await cur.fetchone():
        await db.execute(
            "update settings set value = ? where guild_id = ? and key = ?", (value, guild_id, key))
    else:
        await db.execute(
            "insert into settings (guild_id, key, value) values (?, ?, ?)", (guild_id, key, value))
    await db.commit()
    await db.close()


async def get_setting(server_id: int, key: str, default: str) -> str:
    await db_init()
    return await db_get_key(server_id, key) or default


async def set_setting(server_id: int, key: str, value: str) -> None:
    await db_init()
    await db_set_key(server_id, key, value)
