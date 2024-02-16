import os
import discord
import csv

from discord.ext import commands as commands_ext

class BlockedUserError(commands_ext.CheckFailure):
    def __init__(self, *args: object, reason: str) -> None:
        super().__init__(*args)
        self.reason = reason

class BlockedServerError(commands_ext.CheckFailure):
    def __init__(self, *args: object, reason: str) -> None:
        super().__init__(*args)
        self.reason = reason

def read_blocked_users_file():
    blocks = []
    
    if not os.path.exists('data'):
        os.mkdir('data')
    if not os.path.exists('data/blocklist'):
        os.mkdir('data/blocklist')
    if not os.path.exists('data/blocklist/users.csv'):
        with open('data/blocklist/users.csv', 'w', encoding='utf8') as f:
            f.write()
    with open('data/blocklist/users.csv', 'r', encoding='utf8') as f:
        reader = csv.reader(f, delimiter=';')
        blocks = [row for row in reader]
    
    return blocks

def read_blocked_servers_file():
    blocks = []
    
    if not os.path.exists('data'):
        os.mkdir('data')
    if not os.path.exists('data/blocklist'):
        os.mkdir('data/blocklist')
    if not os.path.exists('data/blocklist/servers.csv'):
        with open('data/blocklist/servers.csv', 'w', encoding='utf8') as f:
            f.write()
    with open('data/blocklist/servers.csv', 'r', encoding='utf8') as f:
        reader = csv.reader(f, delimiter=';')
        blocks = [row for row in reader]
    
    return blocks


def is_blocked():
    
    def predicate(ctx: commands_ext.Context):
        if str(ctx.author.id) in [id for id, _ in read_blocked_users_file()]:
            raise BlockedUserError(reason='You are blocked from using this bot. Reason: ' + [reasn for id, reasn in read_blocked_users_file() if id == str(ctx.author.id)][0])
    
        if ctx.guild is not None and str(ctx.guild.id) in [id for id, _ in read_blocked_servers_file()]:
            raise BlockedServerError(reason='This server is blocked from using this bot (not you :3). Reason: ' + [reasn for id, reasn in read_blocked_servers_file() if id == str(ctx.guild.id)][0])
            
        return True
    
    return commands_ext.check(predicate)
    