def get_key(key: str, default: str = ""):
    with open("config.conf", "r") as f:
        data = f.read()

    for line in data.split("\n"):
        if line.startswith(key):
            return line.split("=")[1].strip()

    # add key with default
    with open("config.conf", "a") as f:
        if not data.endswith("\n"):
            f.write("\n")
        f.write(f"{key}={default}\n")

    return default
