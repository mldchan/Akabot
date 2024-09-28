import datetime

import aiosqlite

from database import get_conn


def calculate_age(birthday: datetime.datetime) -> int:
    return (datetime.datetime.now() - birthday).days // 365


async def create_database():
    db = await get_conn()
    await db.execute('CREATE TABLE IF NOT EXISTS birthdays (user_id integer primary key, current_age int, birthday text)')
    await db.commit()
    await db.close()


async def get_age_of_user(user_id: int) -> int | None:
    db = await get_conn()
    cur = await db.execute('SELECT birthday FROM birthdays WHERE user_id = ?', (user_id,))
    row = await cur.fetchone()
    await db.close()

    if row:
        birthday = datetime.datetime.strptime(row[0], '%m-%d')
        return (datetime.datetime.now() - birthday).days // 365

    return None


async def get_last_age_of_user(user_id: int) -> int | None:
    db = await get_conn()
    cur = await db.execute('SELECT current_age FROM birthdays WHERE user_id = ?', (user_id,))
    row = await cur.fetchone()
    await db.close()

    if row:
        return row[0]

    return None


async def get_birthday(user_id: int) -> str | None:
    db = await get_conn()
    cur = await db.execute('SELECT birthday FROM birthdays WHERE user_id = ?', (user_id,))
    row = await cur.fetchone()
    await db.close()

    if row:
        return row[0]

    return None


async def set_birthday(user_id: int, birthday: datetime.datetime):
    db = await get_conn()
    age = calculate_age(birthday)
    birthday_str = '{:02d}-{:02d}'.format(birthday.month, birthday.day)
    await db.execute('INSERT INTO birthdays (user_id, current_age, birthday) VALUES (?, ?, ?) ON CONFLICT(user_id) DO UPDATE SET current_age=excluded.current_age, birthday=excluded.birthday',
                     (user_id, age, birthday_str))
    await db.commit()
    await db.close()


async def remove_birthday(user_id: int):
    db = await get_conn()
    await db.execute('DELETE FROM birthdays WHERE user_id = ?', (user_id,))
    await db.commit()
    await db.close()


async def get_birthdays_today() -> list[aiosqlite.Row]:
    db = await get_conn()
    now = '{:02d}-{:02d}'.format(datetime.datetime.now().month, datetime.datetime.now().day)
    cur = await db.execute('SELECT * FROM birthdays WHERE birthday = ?', (now,))
    rows = await cur.fetchall()
    await db.close()
    return rows
