import json
import logging
import os.path

from utils.per_user_settings import get_per_user_setting, set_per_user_setting
from utils.settings import get_setting, set_setting
from utils.tips import append_tip_to_message


def get_translation_for_key_localized(user_id: int, guild_id: int, key: str, append_tip=False) -> str:
    """Get translation for a key in the user's language, server language, or English

    Args:
        user_id (int): User ID, if 0, will skip user language
        guild_id (int): Guild ID, if 0, will skip server language
        key (str): Key

    Returns:
        str: Translation
    """
    translation = ""
    language = get_language(guild_id, user_id)

    with open(f"lang/{language}.json", encoding='utf8') as f:
        translations: dict = json.load(f)

    translation = translations.get(key, translation)

    if append_tip and get_per_user_setting(user_id, "tips_enabled", "true") == "true":
        return append_tip_to_message(guild_id, user_id, translation, language)
    return translation


def get_language(guild_id: int, user_id: int) -> str:
    """Get the language for a user, guild or use English as a
    fallback

    Args:
        guild_id (int): Guild ID
        user_id (int): User ID

    Returns:
        str: Language code
    """

    # Get user language
    if user_id != 0:
        user_lang = get_per_user_setting(user_id, "language", "en")
        if not os.path.exists(f"lang/{user_lang}.json"):
            set_per_user_setting(user_id, "language", "en")
            logging.error(
                "WARNING: User {id} has somehow set the user language to {lang}, which is not a valid language. "
                "Reset to EN".format(id=user_id, lang=user_lang))
        return user_lang

    # Get server language
    if guild_id != 0:
        server_lang = get_setting(guild_id, "language", "en")
        if not os.path.exists(f"lang/{server_lang}.json"):
            set_setting(guild_id, "language", "en")
            logging.error(
                "WARNING: Server {id} has somehow set the server language to {lang}, which is not a valid language. "
                "Reset to EN".format(id=guild_id, lang=server_lang))
        return server_lang

    # Global (English)
    return "en"


def get_list_of_languages():
    """Get a list of languages

    Returns:
        list: List of languages
    """
    languages = []
    for file in os.listdir("lang"):
        if file.endswith(".json"):
            languages.append(file[:-5])

    return languages


def get_language_completeness(lang: str) -> int:
    """Returns the percentage of translations completed

    Returns:
        int: Percentage of translations completed
    """
    # Validate lang exists
    if not os.path.exists(f"lang/{lang}.json"):
        raise ValueError("Language does not exist")

    # Load English translations
    with open("lang/en.json", encoding='utf8') as f:
        en_translations: dict = json.load(f)

    # Load target language
    with open(f"lang/{lang}.json", encoding='utf8') as f:
        lang_translations: dict = json.load(f)

    total = len(en_translations)
    translated = 0

    for i in zip(en_translations.values(), lang_translations.values()):
        if i[0].strip() != i[1].strip():
            translated += 1

    return int((translated / total) * 100)


def get_language_name(lang_code: str, completeness: bool = True) -> str:
    """Get the language name from the language code
    Format: English - 100%

    Returns:
        str: Language name
    """

    if lang_code == 'en':
        return 'English'

    # Validate lang exists
    if not os.path.exists(f"lang/{lang_code}.json"):
        raise ValueError("Language does not exist")

    with open(f"lang/{lang_code}.json", encoding='utf8') as f:
        name = json.load(f).get("language", lang_code)

    completeness_percent = get_language_completeness(lang_code)
    if completeness:
        return f"{name} - {completeness_percent}%"
    else:
        return name


def get_language_names() -> list[str]:
    """Get a list of language names

    Returns:
        list: List of language names
    """

    # Generate a list of language names using get_language_name and return it

    languages = []
    for i in get_list_of_languages():
        languages.append(get_language_name(i))

    return languages


def language_name_to_code(lang_name: str) -> str:
    """Get the language code from the language name

    Returns:
        str: Language code
    """

    # Generate a list of language names using get_language_name and return it

    for i in get_list_of_languages():
        if get_language_name(i) == lang_name:
            return i

    return 'en'
