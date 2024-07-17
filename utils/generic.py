import datetime

from utils.languages import get_translation_for_key_localized as trl


def pretty_time_delta(seconds: int | float, user_id: int, server_id: int) -> str:
    seconds = abs(int(seconds))
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days > 0:
        return trl(user_id, server_id, "pretty_time_delta_4").format(days=days, hours=hours, minutes=minutes,
                                                                     seconds=seconds)
    elif hours > 0:
        return trl(user_id, server_id, "pretty_time_delta_3").format(hours=hours, minutes=minutes, seconds=seconds)
    elif minutes > 0:
        return trl(user_id, server_id, "pretty_time_delta_2").format(minutes=minutes, seconds=seconds)
    else:
        return trl(user_id, server_id, "pretty_time_delta_1").format(seconds=seconds)


def pretty_time(seconds_since_epoch: int | float) -> str:
    return datetime.datetime.fromtimestamp(seconds_since_epoch).strftime('%Y/%m/%d %H:%M:%S')


def get_date_time_str() -> str:
    # format: yyyy/mm/dd hh:mm
    return datetime.datetime.now(datetime.UTC).strftime('%Y/%m/%d %H:%M')
