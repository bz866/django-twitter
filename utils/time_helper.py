from datetime import (
    datetime,
)
import pytz
from django.conf import settings


def utc_now():
    return pytz.utc.localize(datetime.now())
    # local_tz = pytz.timezone(settings.TIME_ZONE)
    #
    # local_datetime = local_tz.localize(datetime.now(), is_dst=None)
    # utc_datetime = local_datetime.astimezone(pytz.UTC)
    # return utc_datetime