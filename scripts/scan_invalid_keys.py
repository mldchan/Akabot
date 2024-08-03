import json
import os
import re


def get_files(path: str) -> list[str]:
    # Get list of .py files, recursively in directories

    files = []
    for root, _, filenames in os.walk(path):
        for filename in filenames:
            if filename.endswith('.py'):
                files.append(os.path.join(root, filename))

    return files


if __name__ == '__main__':
    print("Scanning for invalid translation keys...")

    with open("../lang/en.json", "r") as f:
        translations = json.load(f)

    files = get_files("../")

    used_keys = []
    for i in files:
        with open(i, "r", encoding='utf8') as f:
            content = f.read()

        for j in re.findall('trl[(](.*?), (.*?), "(.*?)"[)]', content):
            used_keys.append(j[2])

    invalid_keys = []
    for i in used_keys:
        if i not in translations:
            invalid_keys.append(i)

    print("Invalid keys:", invalid_keys)
