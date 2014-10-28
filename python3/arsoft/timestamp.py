#!/usr/bin/python
# -*- coding: utf-8 -*-
# kate: space-indent on; indent-width 4; mixedindent off; indent-mode python;

from datetime import datetime, timedelta, tzinfo
import time
import re
import math

# Adapted from http://delete.me.uk/2005/03/iso8601.html
ISO8601_REGEX = re.compile(r"(?P<year>[0-9]{4})((?P<month>[0-9]{2})((?P<day>[0-9]{2})"
    r"((?P<hour>[0-9]{2})(?P<minute>[0-9]{2})((?P<second>[0-9]{2})(\.(?P<fraction>[0-9]+))?)?"
    r"(?P<timezone>Z|(([-+])([0-9]{2}):([0-9]{2})))?)?)?)?"
)
TIMEZONE_REGEX = re.compile("(?P<prefix>[+-])(?P<hours>[0-9]{2}).(?P<minutes>[0-9]{2})")
TIMEDELTA_REGEX = re.compile(r'((?P<days>\d+?)d)?((?P<hours>\d+?)hr)?((?P<minutes>\d+?)m)?((?P<seconds>\d+?)s)?')

SECONDS_ONE_MINUTE = 60
SECONDS_ONE_HOUR = 60 * SECONDS_ONE_MINUTE
SECONDS_ONE_DAY = 24 * SECONDS_ONE_HOUR
SECONDS_ONE_WEEK = 7 * SECONDS_ONE_DAY
SECONDS_ONE_MONTH = 30 * SECONDS_ONE_DAY
SECONDS_ONE_YEAR = 365 * SECONDS_ONE_DAY

class ParseError(Exception):
    """Raised when there is a problem parsing a date string"""

# Yoinked from python docs
ZERO = timedelta(0)
class Utc(tzinfo):
    """UTC
    
    """
    def utcoffset(self, dt):
        return ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return ZERO
UTC = Utc()

class FixedOffset(tzinfo):
    """Fixed offset in hours and minutes from UTC
    
    """
    def __init__(self, offset_hours, offset_minutes, name):
        self.__offset = timedelta(hours=offset_hours, minutes=offset_minutes)
        self.__name = name

    def utcoffset(self, dt):
        return self.__offset

    def tzname(self, dt):
        return self.__name

    def dst(self, dt):
        return ZERO
    
    def __repr__(self):
        return "<FixedOffset %r>" % self.__name

def parse_timezone(tzstring, default_timezone=UTC):
    """Parses ISO 8601 time zone specs into tzinfo offsets
    
    """
    if tzstring == "Z":
        return default_timezone
    # This isn't strictly correct, but it's common to encounter dates without
    # timezones so I'll assume the default (which defaults to UTC).
    # Addresses issue 4.
    if tzstring is None:
        return default_timezone
    m = TIMEZONE_REGEX.match(tzstring)
    prefix, hours, minutes = m.groups()
    hours, minutes = int(hours), int(minutes)
    if prefix == "-":
        hours = -hours
        minutes = -minutes
    return FixedOffset(hours, minutes, tzstring)

def parse_date(datestring, default_timezone=UTC):
    """Parses ISO 8601 dates into datetime objects
    
    The timezone is parsed from the date string. However it is quite common to
    have dates without a timezone (not strictly correct). In this case the
    default timezone specified in default_timezone is used. This is UTC by
    default.
    """
    if not isinstance(datestring, str):
        raise ParseError("Expecting a string %r" % datestring)
    m = ISO8601_REGEX.match(datestring)
    if not m:
        raise ParseError("Unable to parse date string %r" % datestring)
    groups = m.groupdict()
    tz = parse_timezone(groups["timezone"], default_timezone=default_timezone)
    if groups["fraction"] is None:
        groups["fraction"] = 0
    else:
        groups["fraction"] = int(float("0.%s" % groups["fraction"]) * 1e6)
    return datetime(int(groups["year"]), int(groups["month"]), int(groups["day"]),
        int(groups["hour"]), int(groups["minute"]), int(groups["second"]),
        int(groups["fraction"]), tz)

def parse_timedelta(time_str):
    parts = TIMEDELTA_REGEX.match(time_str)
    if not parts:
        return None
    parts = parts.groupdict()
    time_params = {}
    for (name, param) in parts.items():
        if param:
            time_params[name] = int(param)
    return timedelta(**time_params)

def format_timedelta(delta):

    if isinstance(delta, timedelta):
        secs = abs(delta.total_seconds())
        is_negative = delta.total_seconds() < 0
    else:
        secs = abs(delta)
        is_negative = delta < 0
    if secs >= SECONDS_ONE_YEAR:
        years = int(secs / SECONDS_ONE_YEAR)
        remain = math.fmod(secs, SECONDS_ONE_YEAR)
        months = int(remain / SECONDS_ONE_MONTH)
        remain = math.fmod(remain, SECONDS_ONE_MONTH)
        days = int(remain / SECONDS_ONE_DAY)
        ret = '%i years, %i months, %i days' % (years, months, days)
    elif secs >= SECONDS_ONE_MONTH:
        months = int(secs / SECONDS_ONE_MONTH)
        remain = math.fmod(secs, SECONDS_ONE_MONTH)
        days = int(remain / SECONDS_ONE_DAY)
        ret = '%i months, %i days' % (months, days)
    elif secs >= SECONDS_ONE_WEEK:
        days = int(secs / SECONDS_ONE_DAY)
        ret = '%i days' % (days)
    elif secs >= SECONDS_ONE_DAY:
        days = int(secs / SECONDS_ONE_DAY)
        remain = math.fmod(secs, SECONDS_ONE_DAY)
        hours = int(remain / SECONDS_ONE_HOUR)
        ret = '%i days, %i hours' % (days, hours)
    elif secs >= SECONDS_ONE_HOUR:
        hours = int(secs / SECONDS_ONE_HOUR)
        remain = math.fmod(secs, SECONDS_ONE_HOUR)
        minutes = int(remain / SECONDS_ONE_MINUTE)
        ret = '%i hours, %i minutes' % (hours, minutes)
    elif secs >= SECONDS_ONE_MINUTE:
        minutes = int(secs / SECONDS_ONE_MINUTE)
        remain = math.fmod(secs, SECONDS_ONE_MINUTE)
        ret = '%i minutes, %i seconds' % (minutes, remain)
    else:
        ret = '%i seconds' % (secs)
    if is_negative:
        ret += ' ago'
    return ret

_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)

def timestamp_from_datetime(datetime_obj):
    "Return POSIX timestamp as float"
    if datetime_obj.tzinfo is None:
        return time.mktime((datetime_obj.year, datetime_obj.month, datetime_obj.day,
                                datetime_obj.hour, datetime_obj.minute, datetime_obj.second,
                                -1, -1, -1)) + datetime_obj.microsecond / 1e6
    else:
        return (datetime_obj - _EPOCH).total_seconds()

SPACE = ' '
EMPTYSTRING = ''
COMMASPACE = ', '

# Parse a date field
_monthnames = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul',
               'aug', 'sep', 'oct', 'nov', 'dec',
               'january', 'february', 'march', 'april', 'may', 'june', 'july',
               'august', 'september', 'october', 'november', 'december']

_daynames = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']

# The timezone table does not include the military time zones defined
# in RFC822, other than Z.  According to RFC1123, the description in
# RFC822 gets the signs wrong, so we can't rely on any such time
# zones.  RFC1123 recommends that numeric timezone indicators be used
# instead of timezone names.

_timezones = {'UT':0, 'UTC':0, 'GMT':0, 'Z':0,
              'AST': -400, 'ADT': -300,  # Atlantic (used in Canada)
              'EST': -500, 'EDT': -400,  # Eastern
              'CST': -600, 'CDT': -500,  # Central
              'MST': -700, 'MDT': -600,  # Mountain
              'PST': -800, 'PDT': -700   # Pacific
              }


def _parsedate_rfc2822(data):
    """Convert a date string to a time tuple.

    Accounts for military timezones.
    """
    data = data.split()
    # The FWS after the comma after the day-of-week is optional, so search and
    # adjust for this.
    if data[0].endswith(',') or data[0].lower() in _daynames:
        # There's a dayname here. Skip it
        del data[0]
    else:
        i = data[0].rfind(',')
        if i >= 0:
            data[0] = data[0][i+1:]
    if len(data) == 3: # RFC 850 date, deprecated
        stuff = data[0].split('-')
        if len(stuff) == 3:
            data = stuff + data[1:]
    if len(data) == 4:
        s = data[3]
        i = s.find('+')
        if i > 0:
            data[3:] = [s[:i], s[i+1:]]
        else:
            data.append('') # Dummy tz
    if len(data) < 5:
        return None
    data = data[:5]
    [dd, mm, yy, tm, tz] = data
    mm = mm.lower()
    if mm not in _monthnames:
        dd, mm = mm, dd.lower()
        if mm not in _monthnames:
            return None
    mm = _monthnames.index(mm) + 1
    if mm > 12:
        mm -= 12
    if dd[-1] == ',':
        dd = dd[:-1]
    i = yy.find(':')
    if i > 0:
        yy, tm = tm, yy
    if yy[-1] == ',':
        yy = yy[:-1]
    if not yy[0].isdigit():
        yy, tz = tz, yy
    if tm[-1] == ',':
        tm = tm[:-1]
    tm = tm.split(':')
    if len(tm) == 2:
        [thh, tmm] = tm
        tss = '0'
    elif len(tm) == 3:
        [thh, tmm, tss] = tm
    else:
        return None
    try:
        yy = int(yy)
        dd = int(dd)
        thh = int(thh)
        tmm = int(tmm)
        tss = int(tss)
    except ValueError:
        return None
    # Check for a yy specified in two-digit format, then convert it to the
    # appropriate four-digit format, according to the POSIX standard. RFC 822
    # calls for a two-digit yy, but RFC 2822 (which obsoletes RFC 822)
    # mandates a 4-digit yy. For more information, see the documentation for
    # the time module.
    if yy < 100:
        # The year is between 1969 and 1999 (inclusive).
        if yy > 68:
            yy += 1900
        # The year is between 2000 and 2068 (inclusive).
        else:
            yy += 2000
    tzoffset = None
    tz = tz.upper()
    if tz in _timezones:
        tzoffset = _timezones[tz]
    else:
        try:
            tzoffset = int(tz)
        except ValueError:
            pass
    # Convert a timezone offset into seconds ; -0500 -> -18000
    if tzoffset:
        if tzoffset < 0:
            tzsign = -1
            tzoffset = -tzoffset
        else:
            tzsign = 1
        tzoffset = tzsign * ( (tzoffset//100)*3600 + (tzoffset % 100)*60)
    # Daylight Saving Time flag is set to -1, since DST is unknown.
    return yy, mm, dd, thh, tmm, tss, 0, 1, -1, tzoffset

def parsedate_rfc2822(data):
    t = _parsedate_rfc2822(data)
    if t is None:
        return None
    else:
        return datetime.fromtimestamp(time.mktime(t))

def strptime_as_datetime(timestamp, format):
    tzoffset = None
    if '%z' in format:
        data = timestamp.split(' ')
        tz = data[-1].upper()
        tz = tz.upper()
        if tz in _timezones:
            tzoffset = _timezones[tz]
        else:
            try:
                tzoffset = int(tz)
            except ValueError:
                pass
        # Convert a timezone offset into seconds ; -0500 -> -18000
        if tzoffset:
            if tzoffset < 0:
                tzsign = -1
                tzoffset = -tzoffset
            else:
                tzsign = 1
            tzoffset = tzsign * ( (tzoffset//100)*60 + (tzoffset % 100))
        format = format.replace(' %z', '')
        format = format.replace('%z', '')
        timestamp = ' '.join(data[:-1])
    t = time.strptime(timestamp, format)
    if t is None:
        return None
    if tzoffset is not None:
        ret = datetime.fromtimestamp(time.mktime(t), FixedOffset(offset_hours=0, offset_minutes=tzoffset, name=None))
    else:
        ret = datetime.fromtimestamp(time.mktime(t))
    return ret

if __name__ == "__main__":

    now = time.time()
    begin_of_time = 0
    last_month = - SECONDS_ONE_MONTH - SECONDS_ONE_DAY
    last_week = - SECONDS_ONE_WEEK - SECONDS_ONE_DAY

    for t in [0, -1, 1, now - begin_of_time, begin_of_time - now, last_month, last_week, SECONDS_ONE_WEEK - SECONDS_ONE_DAY]:
        print('timedelta=%s => %s' % (str(t), format_timedelta(t)))

