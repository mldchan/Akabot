from discord.ext import commands as commands_ext

from database import get_conn


async def db_init():
    db = await get_conn()
    await db.execute("""create table if not exists analytics
(
    command   text
        constraint analytics_pk
            primary key,
    run_count integer
);""")
    await db.commit()
    await db.close()


async def db_add_analytics(command: str):
    await db_init()
    db = await get_conn()
    cur = await db.execute("SELECT run_count FROM analytics WHERE command = ?", (command,))
    data = await cur.fetchone()
    if data:
        await db.execute("UPDATE analytics SET run_count = ? WHERE command = ?", (data[0] + 1, command))
    else:
        await db.execute("INSERT INTO analytics (command, run_count) VALUES (?, ?)", (command, 1))
    await db.commit()
    await db.close()


def analytics(command: str):
    def predicate(ctx: commands_ext.Context):
        async def async_def():
            await db_init()
            await db_add_analytics(command)

        ctx.bot.loop.create_task(async_def(), name='analytics')
        return True

    return commands_ext.check(predicate)
