# ------------------------------------------------------------------------------
# Google Calendar Page Export Handler
# ------------------------------------------------------------------------------
import datetime as dt
from collections import OrderedDict
from urllib.parse import urlencode
import pytz
from icalendar import vPeriod
from django.http import HttpResponseRedirect
from ..models import (
    SimpleEventPage,
    MultidayEventPage,
    RecurringEventPage,
    EventExceptionBase,
)
from ..utils.telltime import getAwareDatetime

# ------------------------------------------------------------------------------


def get_timezone_name(tz):
    """Get timezone name compatible with both pytz and zoneinfo"""
    if hasattr(tz, "zone"):
        # pytz timezone
        return tz.zone
    elif hasattr(tz, "key"):
        # zoneinfo.ZoneInfo timezone
        return tz.key
    else:
        # fallback - convert to string and hope for the best
        return str(tz)


# ------------------------------------------------------------------------------
class GoogleCalendarHandler:
    """Redirect to a new Google Calendar event"""

    def serve(self, page, request, *args, **kwargs):
        gevent = self._makeFromPage(page)
        if gevent:
            return HttpResponseRedirect(gevent.url)

    def _makeFromPage(self, page):
        if isinstance(page, SimpleEventPage):
            return SimpleGEvent.fromPage(page)
        elif isinstance(page, MultidayEventPage):
            return MultidayGEvent.fromPage(page)
        elif isinstance(page, RecurringEventPage):
            return RecurringGEvent.fromPage(page)
        elif isinstance(page, EventExceptionBase):
            return RecurringGEvent.fromPage(page.overrides)


# ------------------------------------------------------------------------------
class GEvent(OrderedDict):
    def set(self, name, value):
        if value:
            self[name] = value

    @classmethod
    def fromPage(cls, page):
        gevent = cls()
        gevent.set("action", "TEMPLATE")
        gevent.set("text", page.title)
        gevent.set("details", page.details)
        gevent.set("location", page.location)
        return gevent

    @property
    def url(self):
        retval = "http://www.google.com/calendar/event?"
        retval += urlencode(self)
        return retval


# ------------------------------------------------------------------------------
class SimpleGEvent(GEvent):
    @classmethod
    def fromPage(cls, page):
        gevent = super().fromPage(page)
        dtstart = getAwareDatetime(page.date, page.time_from, page.tz, dt.time.min)
        dtend = getAwareDatetime(page.date, page.time_to, page.tz, dt.time.max)
        gevent.set("dates", vPeriod((dtstart, dtend)).to_ical().decode())
        if page.tz != pytz.utc:
            gevent.set("ctz", get_timezone_name(page.tz))
        return gevent


# ------------------------------------------------------------------------------
class MultidayGEvent(GEvent):
    @classmethod
    def fromPage(cls, page):
        gevent = super().fromPage(page)
        dtstart = getAwareDatetime(page.date_from, page.time_from, page.tz, dt.time.min)
        dtend = getAwareDatetime(page.date_to, page.time_to, page.tz, dt.time.max)
        gevent.set("dates", vPeriod((dtstart, dtend)).to_ical().decode())
        if page.tz != pytz.utc:
            gevent.set("ctz", get_timezone_name(page.tz))
        return gevent


# ------------------------------------------------------------------------------
class RecurringGEvent(GEvent):
    @classmethod
    def fromPage(cls, page):
        gevent = super().fromPage(page)
        minDt = pytz.utc.localize(dt.datetime.min)
        dtstart = page._getMyFirstDatetimeFrom() or minDt
        dtend = page._getMyFirstDatetimeTo() or minDt
        gevent.set("dates", vPeriod((dtstart, dtend)).to_ical().decode())
        if page.tz != pytz.utc:
            gevent.set("ctz", get_timezone_name(page.tz))
        gevent.set("recur", "RRULE:" + page.repeat._getRrule())
        return gevent


# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
