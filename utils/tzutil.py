import datetime

from utils.settings import get_setting


def get_server_midnight_time(server_id: int) -> datetime:
    """Get the time at midnight for the server's timezone

    Args:
        server_id (int): Server ID

    Returns:
        datetime: Time at midnight
    """
    tz_offset = get_setting(server_id, "timezone_offset", "0")
    stamp1 = datetime.datetime.now(datetime.UTC).timestamp() // 86400 * 86400 + (86400 * 3) + float(tz_offset) * 3600
    return datetime.datetime.fromtimestamp(stamp1)


def adjust_time_for_server(time: datetime, server_id: int) -> datetime:
    """Adjust time for the server's timezone

    Args:
        time (datetime): Time
        server_id (int): Server ID

    Returns:
        datetime: Adjusted time
    """
    tz_offset = get_setting(server_id, "timezone_offset", "0")
    return time + datetime.timedelta(hours=float(tz_offset))


def get_now_for_server(server_id: int) -> datetime:
    """Get the current time for the server's timezone

    Args:
        server_id (int): Server ID

    Returns:
        datetime: Current time
    """
    return adjust_time_for_server(datetime.datetime.now(), server_id)
