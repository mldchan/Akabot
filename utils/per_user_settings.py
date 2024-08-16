from database import conn


def db_init():
    conn.execute("CREATE TABLE IF NOT EXISTS per_user_settings (id integer primary key autoincrement, user_id INTEGER, setting_name TEXT, setting_value TEXT)")
    conn.commit()


def get_per_user_setting(user_id: int, setting_name: str, default_value: str) -> str:
    cur = conn.cursor()
    cur.execute("SELECT setting_value FROM per_user_settings WHERE user_id = ? AND setting_name = ?", (user_id, setting_name))
    row = cur.fetchone()
    if row:
        return row[0]

    cur.execute("INSERT INTO per_user_settings (user_id, setting_name, setting_value) VALUES (?, ?, ?)", (user_id, setting_name, default_value))
    conn.commit()
    return default_value


def set_per_user_setting(user_id: int, setting_name: str, setting_value: str):
    cur = conn.cursor()
    cur.execute("SELECT setting_value FROM per_user_settings WHERE user_id = ? AND setting_name = ?", (user_id, setting_name))
    row = cur.fetchone()
    if row:
        cur.execute("UPDATE per_user_settings SET setting_value = ? WHERE user_id = ? AND setting_name = ?", (setting_value, user_id, setting_name))
    else:
        cur.execute("INSERT INTO per_user_settings (user_id, setting_name, setting_value) VALUES (?, ?, ?)", (user_id, setting_name, setting_value))
    conn.commit()


def unset_per_user_setting(user_id: int, setting_name: str):
    cur = conn.cursor()
    cur.execute("DELETE FROM per_user_settings WHERE user_id = ? AND setting_name = ?", (user_id, setting_name))
    conn.commit()


def search_settings_by_value(setting_value: str):
    """Searches for settings
    Returns: List of settings with the given value
    user_id, setting_name, setting_value order
    """
    cur = conn.cursor()
    cur.execute("SELECT user_id, setting_name, setting_value FROM per_user_settings WHERE setting_value = ?", (setting_value,))
    rows = cur.fetchall()
    return rows
