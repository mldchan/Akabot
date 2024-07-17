import json

print("Akabot Config Converter from 3.1 -> 3.2")
print("This script will convert your config.json to config.conf format.")

with open("config.json", "r") as f:
    data = json.load(f)

with open("config.conf", "w") as f:
    f.write("""
Admin_AdminGuildID={admin_guild}
Admin_OwnerID={owner_id}
Bot_Version=3.2
Sentry_Enabled={sentry_enabled}
Sentry_DSN={sentry_dsn}
Heartbeat_Enabled={heartbeat_enabled}
Bot_Token={token}
GitHub_User={github_user}
GitHub_Repo={github_repo}
GitHub_Token={github_token}
""".format(
                admin_guild=data.get_files("admin_guild", "0"),
                owner_id=data.get_files("owner_id", "0"),
                sentry_enabled=data.get_files("sentry", {}).get_files("enabled", "false"),
                sentry_dsn=data.get_files("sentry", {}).get_files("dsn", ""),
                heartbeat_enabled=data.get_files("heartbeat", {}).get_files("enabled", "false"),
                token=data.get_files("token", ""),
                github_user=data.get_files("github", {}).get_files("git_user", ""),
                github_repo=data.get_files("github", {}).get_files("git_repo", ""),
                github_token=data.get_files("github", {}).get_files("token", "")
            ))
    
print("Conversion complete. Written to config.conf.")