import json

print("Akabot Config Converter from 3.1 -> 3.2")
print("This script will convert your config.json to config.conf format.")

# New config
# Admin_AdminGuildID=
# Admin_OwnerID=
# Bot_Version=
# Sentry_Enabled=
# Sentry_DSN=
# Heartbeat_Enabled=
# Bot_Token=
# Feature_DatabaseCleanupTask=
# Feature_WelcomeGoodbye=
# Feature_Leveling=
# Feature_AntiRaid=
# Feature_ChatStreaks=
# Feature_ChatRevive=
# Feature_ChatSummary=
# Feature_ReactionRoles=
# Feature_Logging=
# Feature_AdminCommands=
# Feature_Giveaways=
# Feature_FeedbackCmd=
# Feature_Moderation=
# Feature_Verification=
# Feature_VelkyStompies=
# Feature_RolesOnJoin=
# Feature_Heartbeat=
# Feature_AutomodActions=
# GitHub_User=
# GitHub_Repo=
# GitHub_Token=
# Old config
# {
#     "token": "token",
#     "owner_id": 0,
#     "admin_guild": 0,
#     "github": {
#         "token": "",
#         "git_repo": "",
#         "git_user": ""
#     },
#     "sentry": {
#         "enabled": false,
#         "dsn": ""
#     },
#     "heartbeat": {
#         "enabled": false,
#         "url": "",
#         "method": "post",
#         "interval": 30
#     }
# }

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
                admin_guild=data.get("admin_guild", "0"),
                owner_id=data.get("owner_id", "0"),
                sentry_enabled=data.get("sentry", {}).get("enabled", "false"),
                sentry_dsn=data.get("sentry", {}).get("dsn", ""),
                heartbeat_enabled=data.get("heartbeat", {}).get("enabled", "false"),
                token=data.get("token", ""),
                github_user=data.get("github", {}).get("git_user", ""),
                github_repo=data.get("github", {}).get("git_repo", ""),
                github_token=data.get("github", {}).get("token", "")
            ))
    
print("Conversion complete. Written to config.conf.")