
from database import conn as db


def db_init():
    cur = db.cursor()
    cur.execute("""create table if not exists settings
(
    guild_id integer,
    key      text,
    value    text,
    constraint settings_pk
        primary key (guild_id, key)
);""")
    cur.close()
    db.commit()


def db_get_key(guild_id: int, key: str):
    db_init()
    cur = db.cursor()
    cur.execute(
        "SELECT value FROM settings WHERE guild_id = ? AND key = ?", (guild_id, key))
    result = cur.fetchone()
    cur.close()
    return result[0] if result else None


def db_set_key(guild_id: int, key: str, value: str):
    db_init()
    cur = db.cursor()
    cur.execute(
        "select * from settings where guild_id = ? and key = ?", (guild_id, key))
    if cur.fetchone():
        cur.execute(
            "update settings set value = ? where guild_id = ? and key = ?", (value, guild_id, key))
    else:
        cur.execute(
            "insert into settings (guild_id, key, value) values (?, ?, ?)", (guild_id, key, value))
    cur.close()
    db.commit()


def get_setting(server_id: int, key: str, default: str) -> str:
    db_init()
    return db_get_key(server_id, key) or default


def set_setting(server_id: int, key: str, value: str) -> None:
    db_init()
    db_set_key(server_id, key, value)
