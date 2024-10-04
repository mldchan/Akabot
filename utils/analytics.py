from discord.ext import commands as commands_ext

from database import client


def db_add_analytics(command: str):
    data = client['Analytics'].find_one({'Command': command})
    if data:
        client['Analytics'].update_one({'Command': command}, {'$inc': {'RunCount': 1}})
    else:
        client['Analytics'].insert_one({'Command': command, 'RunCount': 1})


def analytics(command: str):
    def predicate(ctx: commands_ext.Context):
        db_add_analytics(command)
        return True

    return commands_ext.check(predicate)
