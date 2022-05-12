# @CHECK 2.0 features OK
from datetime import datetime as dt
import pytz
from dateutil import parser
from dateutil import tz
from logging import getLogger

log = getLogger("pog_bot")

TZ_OFFSETS = {
    "CEST": +7200,
    "BST": +3600,
    "EDT": -14400,
    "CDT": -18000,
    "MDT": -21600,
    "PDT": -25200,
    "MSK": +10800,
    "AEST": +36000,
    "CST": +28800
}


class UnexpectedError(Exception):
    def __init__(self, msg):
        self.reason = msg
        message = "Encountered unexpected error: " + msg
        log.error(message)
        super().__init__(message)


def is_al_num(string):
    """
    Little utility to check if a string contains only letters and numbers (a-z,A-Z,0-9)

    :param string: The string to be processed
    :return: Result
    """
    for i in string.lower():
        cond = ord('a') <= ord(i) <= ord('z')
        cond = cond or (ord('0') <= ord(i) <= ord('9'))
        if not cond:
            return False
    return True


def date_parser(string):
    try:
        dtx = parser.parse(string, dayfirst=False, tzinfos=TZ_OFFSETS)
    except parser.ParserError:
        return
    try:
        dtx = pytz.utc.localize(dtx)
        dtx = dtx.replace(tzinfo=tz.UTC)
    except ValueError:
        pass
    dtx = dtx.astimezone(pytz.timezone("UTC"))
    return dtx


def timestamp_now():
    return int(dt.timestamp(dt.now()))


def time_diff(timestamp):
    lead = timestamp_now() - timestamp
    if lead < 60:
        lead_str = f"{lead} second"
    elif lead < 3600:
        lead //= 60
        lead_str = f"{lead} minute"
    elif lead < 86400:
        lead //= 3600
        lead_str = f"{lead} hour"
    elif lead < 604800:
        lead //= 86400
        lead_str = f"{lead} day"
    elif lead < 2419200:
        lead //= 604800
        lead_str = f"{lead} week"
    else:
        lead //= 2419200
        lead_str = f"{lead} month"
    if lead > 1:
        return lead_str + "s"
    else:
        return lead_str


def time_calculator(arg: str):
    if arg.endswith(('m', 'month', 'months')):
        time = 2419200
    elif arg.endswith(('w', 'week', 'weeks')):
        time = 604800
    elif arg.endswith(('d', 'day', 'days')):
        time = 86400
    elif arg.endswith(('h', 'hour', 'hours')):
        time = 3600
    elif arg.endswith(('min', 'mins', 'minute', 'minutes')):
        time = 60
    else:
        return 0

    num = ""
    for c in arg:
        if ord('0') <= ord(c) <= ord('9'):
            num += c
        else:
            break

    try:
        time *= int(num)
        if time == 0:
            return 0
    except ValueError:
        return 0

    return time


class AutoDict(dict):
    def auto_add(self, key, value):
        if key in self:
            self[key] += value
        else:
            self[key] = value