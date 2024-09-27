import datetime

from utils.settings import get_setting


async def get_server_midnight_time(server_id: int) -> datetime.datetime:
    """Get the time at midnight for the server's timezone

    Args:
        server_id (int): Server ID

    Returns:
        datetime: Time at midnight
    """
    tz_offset = await get_setting(server_id, "timezone_offset", "0")
    stamp1 = datetime.datetime.now(datetime.UTC).timestamp() // 86400 * 86400 + (86400 * 3) + float(tz_offset) * 3600
    return datetime.datetime.fromtimestamp(stamp1)


async def adjust_time_for_server(time: datetime.datetime, server_id: int) -> datetime.datetime:
    """Adjust time for the server's timezone

    Args:
        time (datetime): Time
        server_id (int): Server ID

    Returns:
        datetime: Adjusted time
    """
    tz_offset = await get_setting(server_id, "timezone_offset", "0")
    return time + datetime.timedelta(hours=float(tz_offset))


async def get_now_for_server(server_id: int) -> datetime.datetime:
    """Get the current time for the server's timezone

    Args:
        server_id (int): Server ID

    Returns:
        datetime: Current time
    """
    return await adjust_time_for_server(datetime.datetime.now(), server_id)
