'''
Source code from: https://docs.python.org/2.7/library/datetime.html#tzinfo-objects
'''
from __future__ import absolute_import
from __future__ import unicode_literals
from datetime import tzinfo, timedelta

ZERO = timedelta(0)


class UTC(tzinfo):
    """UTC"""

    def utcoffset(self, dt):
        return ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return ZERO


utc = UTC()
