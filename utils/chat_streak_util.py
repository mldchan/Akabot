import datetime


def get_time_at_midnight() -> datetime:
    stamp1 = datetime.datetime.now(datetime.UTC).timestamp() // 86400 * 86400 + (86400 * 3)
    return datetime.datetime.fromtimestamp(stamp1)

