import aiosqlite

from database import get_conn


async def db_init():
    db = await get_conn()
    await db.execute("CREATE TABLE IF NOT EXISTS announcement_channels (guild_id BIGINT, channel_id BIGINT)")
    await db.commit()
    await db.close()


async def db_add_announcement_channel(guild_id: int, channel_id: int):
    db = await get_conn()
    await db.execute("INSERT INTO announcement_channels (guild_id, channel_id) VALUES (?, ?)", (guild_id, channel_id))
    await db.commit()
    await db.close()


async def db_remove_announcement_channel(guild_id: int, channel_id: int):
    db = await get_conn()
    await db.execute("DELETE FROM announcement_channels WHERE guild_id = ? AND channel_id = ?", (guild_id, channel_id))
    await db.commit()
    await db.close()


async def db_is_subscribed_to_announcements(guild_id: int, channel_id: int):
    db = await get_conn()
    cur = await db.execute("SELECT * FROM announcement_channels WHERE guild_id = ? AND channel_id = ?", (guild_id, channel_id))
    fetch = await cur.fetchone()
    await db.close()
    return fetch is not None


async def db_get_announcement_channels(guild_id: int):
    db = await get_conn()
    cur = await db.execute("SELECT * FROM announcement_channels WHERE guild_id = ?", (guild_id,))
    fetch_all = await cur.fetchall()
    await db.close()
    return fetch_all


async def db_get_all_announcement_channels():
    db = await get_conn()
    cur = await db.execute("SELECT * FROM announcement_channels")
    fetch_all = await cur.fetchall()
    await db.close()
    return fetch_all
