import random


def verify_english_word(word: str) -> bool:
    with open("data/words.txt") as f:
        text_file = f.read().splitlines()

    for i in text_file:
        if i == word:
            return True

    return False


def get_random_english_word() -> str:
    with open("data/words.txt") as f:
        text_file = f.read().splitlines()

    return random.choice(text_file)
