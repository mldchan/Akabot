from discord.ext import commands as commands_ext

from database import conn as db


def db_init():
    cur = db.cursor()
    cur.execute("""create table if not exists analytics
(
    command   text
        constraint analytics_pk
            primary key,
    run_count integer
);""")
    cur.close()


def db_add_analytics(command: str):
    db_init()
    cur = db.cursor()
    cur.execute("SELECT run_count FROM analytics WHERE command = ?", (command,))
    data = cur.fetchone()
    if data:
        cur.execute("UPDATE analytics SET run_count = ? WHERE command = ?", (data[0] + 1, command))
    else:
        cur.execute("INSERT INTO analytics (command, run_count) VALUES (?, ?)", (command, 1))
    cur.close()
    db.commit()


def analytics(command: str):
    def predicate(ctx: commands_ext.Context):
        db_init()
        db_add_analytics(command)
        return True

    return commands_ext.check(predicate)
