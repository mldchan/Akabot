"""Settings module"""

import os
import json

def read_file(server_id: int):
    if not os.path.exists('data'):
        os.mkdir('data')
    if not os.path.exists('data/settings'):
        os.mkdir('data/settings')
    if not os.path.exists(f'data/settings/{str(server_id)}.json'):
        with open(f'data/settings/{str(server_id)}.json', 'w', encoding='utf8') as f:
            json.dump({}, f)
    with open(f'data/settings/{str(server_id)}.json', 'r', encoding='utf8') as f:
        settings = json.load(f)
    return settings

def write_file(server_id: int, settings):
    if not os.path.exists('data'):
        os.mkdir('data')
    if not os.path.exists('data/settings'):
        os.mkdir('data/settings')
    if os.path.exists(f'data/settings/{str(server_id)}.json'):
        os.remove(f'data/settings/{str(server_id)}.json')
    with open(f'data/settings/{str(server_id)}.json', 'w', encoding='utf8') as f:
        json.dump(settings, f)

def get_setting(server_id: int, key: str, default: str) -> str:
    settings = read_file(server_id)
    return settings[key] if key in settings else default

def set_setting(server_id: int, key: str, value: str) -> None:
    settings = read_file(server_id)
    settings[key] = value
    write_file(server_id, settings)
    