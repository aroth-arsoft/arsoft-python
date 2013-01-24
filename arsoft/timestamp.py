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
    if not isinstance(datestring, basestring):
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
    for (name, param) in parts.iteritems():
        if param:
            time_params[name] = int(param)
    return timedelta(**time_params)

def format_timedelta(delta):
    secs = abs(delta.total_seconds())

    if secs >= SECONDS_ONE_WEEK:
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
    return ret
