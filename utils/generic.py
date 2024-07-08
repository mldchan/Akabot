import datetime


def pretty_time_delta(seconds: int):
    sign_string = '-' if seconds < 0 else ''
    seconds = abs(int(seconds))
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days > 0:
        return '%s%d days %d hours %d minutes and %d seconds' % (sign_string, days, hours, minutes, seconds)
    elif hours > 0:
        return '%s%d hours %d minutes and %d seconds' % (sign_string, hours, minutes, seconds)
    elif minutes > 0:
        return '%s%d minutes and %d seconds' % (sign_string, minutes, seconds)
    else:
        return '%s%d seconds' % (sign_string, seconds)
    
def get_date_time_str() -> str:
    # format: yyyy/mm/dd hh:mm
    return datetime.datetime.now(datetime.UTC).strftime('%Y/%m/%d %H:%M')
