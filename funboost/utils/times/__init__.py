import datetime
import sys

import arrow

from .version import VERSION

PY3 = sys.version_info[0] == 3
if PY3:
    string_types = str
else:
    string_types = basestring


__author__ = 'Vincent Driessen <vincent@3rdcloud.com>'
__version__ = VERSION


def to_universal(local_dt, timezone=None):
    """
    Converts the given local datetime or UNIX timestamp to a universal
    datetime.
    """
    if isinstance(local_dt, (int, float)):
        if timezone is not None:
            raise ValueError('Timezone argument illegal when using UNIX timestamps.')
        return from_unix(local_dt)
    elif isinstance(local_dt, string_types):
        local_dt = arrow.get(local_dt).to('UTC').naive

    return from_local(local_dt, timezone)


def from_local(local_dt, timezone=None):
    """Converts the given local datetime to a universal datetime."""
    if not isinstance(local_dt, datetime.datetime):
        raise TypeError('Expected a datetime object')

    if timezone is None:
        a = arrow.get(local_dt)
    else:
        a = arrow.get(local_dt, timezone)
    return a.to('UTC').naive


def from_unix(ut):
    """
    Converts a UNIX timestamp, as returned by `time.time()`, to universal
    time.  Assumes the input is in UTC, as `time.time()` does.
    """
    if not isinstance(ut, (int, float)):
        raise TypeError('Expected an int or float value')

    return arrow.get(ut).naive


def to_local(dt, timezone):
    """Converts universal datetime to a local representation in given timezone."""
    if dt.tzinfo is not None:
        raise ValueError(
            'First argument to to_local() should be a universal time.'
        )
    if not isinstance(timezone, string_types):
        raise TypeError('expected a timezone name (string), but got {} instead'.format(type(timezone)))
    return arrow.get(dt).to(timezone).datetime


def to_unix(dt):
    """Converts a datetime object to unixtime"""
    if not isinstance(dt, datetime.datetime):
        raise TypeError('Expected a datetime object')

    return arrow.get(dt).timestamp


def format(dt, timezone, fmt=None):
    """Formats the given universal time for display in the given time zone."""
    local = to_local(dt, timezone)
    if fmt is None:
        return local.isoformat()
    else:
        return local.strftime(fmt)


now = datetime.datetime.utcnow
