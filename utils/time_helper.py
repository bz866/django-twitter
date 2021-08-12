from datetime import datetime
import pytz
import time


def ts_now_as_int():
    return int(time.time() * 1000000)

def utc_now():
    return pytz.utc.localize(datetime.now())
    # local_tz = pytz.timezone(settings.TIME_ZONE)
    #
    # local_datetime = local_tz.localize(datetime.now(), is_dst=None)
    # utc_datetime = local_datetime.astimezone(pytz.UTC)
    # return utc_datetime