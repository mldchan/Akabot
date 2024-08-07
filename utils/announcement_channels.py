from database import conn


def db_init():
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS announcement_channels (guild_id BIGINT, channel_id BIGINT)")
    conn.commit()


def db_add_announcement_channel(guild_id: int, channel_id: int):
    cur = conn.cursor()
    cur.execute("INSERT INTO announcement_channels (guild_id, channel_id) VALUES (?, ?)", (guild_id, channel_id))
    conn.commit()


def db_remove_announcement_channel(guild_id: int, channel_id: int):
    cur = conn.cursor()
    cur.execute("DELETE FROM announcement_channels WHERE guild_id = ? AND channel_id = ?", (guild_id, channel_id))
    conn.commit()


def db_is_subscribed_to_announcements(guild_id: int, channel_id: int):
    cur = conn.cursor()
    cur.execute("SELECT * FROM announcement_channels WHERE guild_id = ? AND channel_id = ?", (guild_id, channel_id))
    return cur.fetchone() is not None


def db_get_announcement_channels(guild_id: int):
    cur = conn.cursor()
    cur.execute("SELECT * FROM announcement_channels WHERE guild_id = ?", (guild_id,))
    return cur.fetchall()


def db_get_all_announcement_channels():
    cur = conn.cursor()
    cur.execute("SELECT * FROM announcement_channels")
    return cur.fetchall()
