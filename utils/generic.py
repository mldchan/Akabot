import datetime

from utils.languages import get_translation_for_key_localized as trl
from utils.tzutil import get_now_for_server


async def pretty_time_delta(seconds: int | float, user_id: int, server_id: int, show_seconds=True, show_minutes=True) -> str:
    seconds = abs(int(seconds))
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days > 0:
        # return await trl(user_id, server_id, "pretty_time_delta_4").format(days=days, hours=hours, minutes=minutes,
        #                                                              seconds=seconds)
        if not show_minutes:
            return (await trl(user_id, server_id, "pretty_time_delta_4_no_minutes")).format(days=days, hours=hours)
        elif not show_seconds:
            return (await trl(user_id, server_id, "pretty_time_delta_4_no_seconds")).format(days=days, hours=hours,
                                                                                    minutes=minutes)
        else:
            return (await trl(user_id, server_id, "pretty_time_delta_4")).format(days=days, hours=hours, minutes=minutes,
                                                                         seconds=seconds)
    elif hours > 0:
        # return await trl(user_id, server_id, "pretty_time_delta_3").format(hours=hours, minutes=minutes, seconds=seconds)
        if not show_minutes:
            return (await trl(user_id, server_id, "pretty_time_delta_3_no_minutes")).format(hours=hours)
        elif not show_seconds:
            return (await trl(user_id, server_id, "pretty_time_delta_3_no_seconds")).format(hours=hours, minutes=minutes)
        else:
            return (await trl(user_id, server_id, "pretty_time_delta_3")).format(hours=hours, minutes=minutes, seconds=seconds)
    elif minutes > 0:
        # return await trl(user_id, server_id, "pretty_time_delta_2").format(minutes=minutes, seconds=seconds)
        if not show_minutes:
            return await trl(user_id, server_id, "pretty_time_delta_less_than_an_hour")
        elif not show_seconds:
            return (await trl(user_id, server_id, "pretty_time_delta_2_no_seconds")).format(minutes=minutes)
        else:
            return (await trl(user_id, server_id, "pretty_time_delta_2")).format(minutes=minutes, seconds=seconds)
    else:
        if not show_minutes:
            return await trl(user_id, server_id, "pretty_time_delta_less_than_an_hour")
        elif not show_seconds:
            return await trl(user_id, server_id, "pretty_time_delta_less_than_a_minute")
        else:
            return (await trl(user_id, server_id, "pretty_time_delta_1")).format(seconds=seconds)


def pretty_time(seconds_since_epoch: int | float) -> str:
    return datetime.datetime.fromtimestamp(seconds_since_epoch).strftime('%Y/%m/%d %H:%M:%S')


async def get_date_time_str(guild_id: int) -> str:
    # format: yyyy/mm/dd hh:mm
    return (await get_now_for_server(guild_id)).strftime('%Y/%m/%d %H:%M')
