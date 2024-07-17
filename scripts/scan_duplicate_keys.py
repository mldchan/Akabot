import json

if __name__ == '__main__':
    print("Scanning for duplicate translation keys...")

    with open("../lang/en.json", "r") as f:
        translations = json.load(f)

    duplicate_keys = []

    for key, value in translations.items():
        if list(translations.values()).count(value) > 1:
            duplicate_keys.append(key)

    print("Duplicate keys:", duplicate_keys)
