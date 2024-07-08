import logging

def get_key(key: str, default: str = ""):
    logging.info("Getting config for \"{key}\"".format(key=key))
    with open("config.conf", "r") as f:
        data = f.read()

    for line in data.split("\n"):
        if line.startswith(key):
            logging.info("Found config for \"{key}\" is \"{value}\"".format(key=key, value=line.split("=")[1].strip()))
            return line.split("=")[1].strip()
        
    # add key with default
    with open("config.conf", "a") as f:
        logging.info("Adding config for \"{key}\" with default value \"{default}\"".format(key=key, default=default))
        if not data.endswith("\n"):
            f.write("\n")
        f.write(f"{key}={default}\n")

    return default
