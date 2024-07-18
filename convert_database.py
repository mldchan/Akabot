from database import conn

cur = conn.cursor()

print("Adding winner_count column to giveaways table if it doesn't exist")
# Add winner_count column if it doesn't exist
cur.execute(
    "PRAGMA table_info(giveaways)"
)
columns = cur.fetchall()
column_names = [column[1] for column in columns]
if "winner_count" not in column_names:
    cur.execute(
        "ALTER TABLE giveaways ADD COLUMN winner_count int"
    )

print("Updating giveaway_participants table to have user_id as text")
# Update giveaway_participants table to have user_id as text
cur.execute(
    "PRAGMA table_info(giveaway_participants)"
)
columns = cur.fetchall()
column_names = [column[1] for column in columns]
if "user_id" in column_names:
    cur.execute(
        "ALTER TABLE giveaway_participants RENAME TO giveaway_participants_old"
    )
    cur.execute(
        "create table giveaway_participants(id integer primary key, giveaway_id integer, user_id text)"
    )
    cur.execute(
        "insert into giveaway_participants(giveaway_id, user_id) select giveaway_id, cast(user_id as text) from giveaway_participants_old"
    )
    cur.execute(
        "drop table giveaway_participants_old"
    )

# Auto React table check if the name of the second column is "channel_id", if yes, drop the table
print("Checking if auto_react table exists")
cur.execute(
    "PRAGMA table_info(auto_react)"
)
columns = cur.fetchall()
column_names = [column[1] for column in columns]
if "channel_id" in column_names:
    print("Dropping auto_react table")
    cur.execute("DROP TABLE auto_react")

# Auto Response table check if the name of the second column is "channel_id", if yes, drop the table
print("Checking if auto_response table exists")
cur.execute(
    "PRAGMA table_info(auto_response)"
)
columns = cur.fetchall()
column_names = [column[1] for column in columns]
if "channel_id" in column_names:
    print("Dropping auto_response table")
    cur.execute("DROP TABLE auto_response")

conn.commit()
