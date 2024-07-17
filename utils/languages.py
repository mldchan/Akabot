import json
import logging
import os.path

from utils.per_user_settings import get_per_user_setting, set_per_user_setting
from utils.settings import get_setting, set_setting


def get_translation_for_key(key: str) -> str:
    """Get translation for a key in English

    Args:
        key (str): Key

    Returns:
        str: Translation
    """
    with open("lang/en.json") as f:
        translations = json.load(f)

    return translations.get(key, key)


def get_translation_for_key_localized(user_id: int, guild_id: int, key: str) -> str:
    """Get translation for a key in the user's language, server language, or English

    Args:
        user_id (int): User ID, if 0, will skip user language
        guild_id (int): Guild ID, if 0, will skip server language
        key (str): Key

    Returns:
        str: Translation
    """
    # Get user language
    if user_id != 0:
        user_lang = get_per_user_setting(user_id, "language", "en")
        if not os.path.exists(f"lang/{user_lang}.json"):
            set_per_user_setting(user_id, "language", "en")
            logging.error(
                "WARNING: User {id} has somehow set the user language to {lang}, which is not a valid language. "
                "Reset to EN".format(id=user_id, lang=user_lang))
        with open(f"lang/{user_lang}.json") as f:
            translations = json.load(f)

        if key in translations:
            return translations[key]

    # Get server language
    if guild_id != 0:
        server_lang = get_setting(guild_id, "language", "en")
        if not os.path.exists(f"lang/{server_lang}.json"):
            set_setting(guild_id, "language", "en")
            logging.error(
                "WARNING: Server {id} has somehow set the server language to {lang}, which is not a valid language. "
                "Reset to EN".format(id=guild_id, lang=server_lang))

        with open(f"lang/{server_lang}.json") as f:
            translations = json.load(f)

        if key in translations:
            return translations[key]

    # Global (English)
    with open("lang/en.json") as f:
        translations = json.load(f)

    return translations.get(key, key)
