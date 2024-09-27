from database import get_conn


async def db_init():
    db = await get_conn()
    await db.execute("CREATE TABLE IF NOT EXISTS per_user_settings (id integer primary key autoincrement, user_id INTEGER, setting_name TEXT, setting_value TEXT)")
    await db.commit()
    await db.close()


async def get_per_user_setting(user_id: int, setting_name: str, default_value: str) -> str:
    db = await get_conn()
    cur = await db.execute("SELECT setting_value FROM per_user_settings WHERE user_id = ? AND setting_name = ?", (user_id, setting_name))
    row = await cur.fetchone()
    if row:
        return row[0]

    await db.execute("INSERT INTO per_user_settings (user_id, setting_name, setting_value) VALUES (?, ?, ?)", (user_id, setting_name, default_value))
    await db.commit()
    await db.close()
    return default_value


async def set_per_user_setting(user_id: int, setting_name: str, setting_value: str):
    db = await get_conn()
    cur = await db.execute("SELECT setting_value FROM per_user_settings WHERE user_id = ? AND setting_name = ?", (user_id, setting_name))
    row = await cur.fetchone()
    if row:
        await db.execute("UPDATE per_user_settings SET setting_value = ? WHERE user_id = ? AND setting_name = ?", (setting_value, user_id, setting_name))
    else:
        await db.execute("INSERT INTO per_user_settings (user_id, setting_name, setting_value) VALUES (?, ?, ?)", (user_id, setting_name, setting_value))
    await db.commit()
    await db.close()


async def unset_per_user_setting(user_id: int, setting_name: str):
    db = await get_conn()
    await db.execute("DELETE FROM per_user_settings WHERE user_id = ? AND setting_name = ?", (user_id, setting_name))
    await db.commit()
    await db.close()


async def search_settings_by_value(setting_value: str):
    """Searches for settings
    Returns: List of settings with the given value
    user_id, setting_name, setting_value order
    """
    db = await get_conn()
    cur = await db.execute("SELECT user_id, setting_name, setting_value FROM per_user_settings WHERE setting_value = ?", (setting_value,))
    rows = await cur.fetchall()
    await db.close()
    return rows
