from discord.ext import commands as commands_ext

from database import conn as db
from utils.languages import get_translation_for_key_localized as trl


class BlockedUserError(commands_ext.CheckFailure):
    def __init__(self, *args: object, reason: str) -> None:
        super().__init__(*args)
        self.reason = reason


class BlockedServerError(commands_ext.CheckFailure):
    def __init__(self, *args: object, reason: str) -> None:
        super().__init__(*args)
        self.reason = reason


def db_init():
    cur = db.cursor()
    cur.execute('create table if not exists blocked_users (id int, reason text)')
    cur.execute('create table if not exists blocked_servers (id int, reason text)')
    cur.close()
    db.commit()


def db_check_user_blocked(user_id: int):
    db_init()
    cur = db.cursor()
    cur.execute('select * from blocked_users where id = ?', (user_id,))
    return cur.fetchone() is not None


def db_check_server_blocked(user_id: int):
    db_init()
    cur = db.cursor()
    cur.execute('select * from blocked_servers where id = ?', (user_id,))
    return cur.fetchone() is not None


def db_get_user_blocked_reason(user_id: int):
    db_init()
    cur = db.cursor()
    cur.execute('select reason from blocked_users where id = ?', (user_id,))
    return cur.fetchone()[0]


def db_get_server_blocked_reason(user_id: int):
    db_init()
    cur = db.cursor()
    cur.execute('select reason from blocked_servers where id = ?', (user_id,))
    return cur.fetchone()[0]


def db_add_blocked_user(user_id: int, reason: str):
    db_init()
    cur = db.cursor()
    cur.execute('insert into blocked_users (id, reason) values (?, ?)', (user_id, reason))
    cur.close()
    db.commit()


def db_add_blocked_server(user_id: int, reason: str):
    db_init()
    cur = db.cursor()
    cur.execute('insert into blocked_servers (id, reason) values (?, ?)', (user_id, reason))
    cur.close()
    db.commit()


def db_remove_blocked_user(user_id: int):
    db_init()
    cur = db.cursor()
    cur.execute('delete from blocked_users where id = ?', (user_id,))
    cur.close()
    db.commit()


def db_remove_blocked_server(user_id: int):
    db_init()
    cur = db.cursor()
    cur.execute('delete from blocked_servers where id = ?', (user_id,))
    cur.close()
    db.commit()


def is_blocked():
    def predicate(ctx: commands_ext.Context):
        db_init()
        if db_check_user_blocked(ctx.author.id):
            reason = db_get_user_blocked_reason(ctx.author.id)
            raise BlockedUserError(reason=trl(ctx.author.id, ctx.guild.id, "bot_blocked_user").format(reason=reason))

        if db_check_server_blocked(ctx.guild.id):
            reason = db_get_server_blocked_reason(ctx.guild.id)
            raise BlockedServerError(
                reason=trl(ctx.author.id, ctx.guild.id, "bot_blocked_server").format(reason=reason))

        return True

    return commands_ext.check(predicate)
