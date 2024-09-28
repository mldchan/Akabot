import json
import random
import re


def get_tips_from_lang_file(lang: str) -> list[str]:
    """Get the tips from the language file

    Args:
        lang (str): Language to get tips in (returns empty array when no tips are available for this language)

    Returns:
        list: List of tips
    """
    with open(f"lang/{lang}.json", encoding='utf8') as f:
        file = json.load(f)

    tips = []
    for key in file:
        if re.match(r"^tip_\d+$", key):
            tips.append(file[key])

    return tips


def append_tip_to_message(guild_id: int, user_id: int, msg: str, lang: str) -> str:
    """Append a random tip to a message

    Args:
        guild_id (int): Guild ID
        user_id (int): User ID
        msg (str): Message
        lang (str): Language to get tips in (Will NOT append tip if no tips are available for this language)

    Returns:
        str: Message with tip
    """
    tips = get_tips_from_lang_file(lang)
    if len(tips) == 0:
        return msg  # No tips available for this language

    tip = tips[random.randint(0, len(tips) - 1)]
    return f"{msg}\n\n-# **Tip:** {tip}"
