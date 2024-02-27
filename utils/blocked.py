import os
import discord
import csv

from discord.ext import commands as commands_ext
from database import conn as db


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
    cur.execute(
        'create table if not exists blocked_servers (id int, reason text)')
    cur.close()
    db.commit()


def db_check_user_blocked(id: int):
    db_init()
    cur = db.cursor()
    cur.execute('select * from blocked_users where id = ?', (id,))
    return cur.fetchone() is not None


def db_check_server_blocked(id: int):
    db_init()
    cur = db.cursor()
    cur.execute('select * from blocked_servers where id = ?', (id,))
    return cur.fetchone() is not None


def db_get_user_blocked_reason(id: int):
    db_init()
    cur = db.cursor()
    cur.execute('select reason from blocked_users where id = ?', (id,))
    return cur.fetchone()[0]


def db_get_server_blocked_reason(id: int):
    db_init()
    cur = db.cursor()
    cur.execute('select reason from blocked_servers where id = ?', (id,))
    return cur.fetchone()[0]


def db_add_blocked_user(id: int, reason: str):
    db_init()
    cur = db.cursor()
    cur.execute(
        'insert into blocked_users (id, reason) values (?, ?)', (id, reason))
    cur.close()
    db.commit()


def db_add_blocked_server(id: int, reason: str):
    db_init()
    cur = db.cursor()
    cur.execute(
        'insert into blocked_servers (id, reason) values (?, ?)', (id, reason))
    cur.close()
    db.commit()


def db_remove_blocked_user(id: int):
    db_init()
    cur = db.cursor()
    cur.execute(
        'delete from blocked_users where id = ?', (id,))
    cur.close()
    db.commit()


def db_remove_blocked_server(id: int):
    db_init()
    cur = db.cursor()
    cur.execute(
        'delete from blocked_servers where id = ?', (id,))
    cur.close()
    db.commit()


def is_blocked():
    def predicate(ctx: commands_ext.Context):
        if db_check_user_blocked(ctx.author.id):
            reason = db_get_user_blocked_reason(ctx.author.id)
            raise BlockedUserError(
                reason=f'You are blocked from using this bot. Reason: {reason}')

        if db_check_server_blocked(ctx.guild.id):
            reason = db_get_server_blocked_reason(ctx.guild.id)
            raise BlockedServerError(
                reason=f'This server is blocked from using this bot (not you :3). Reason: {reason}')

        return True

    return commands_ext.check(predicate)
