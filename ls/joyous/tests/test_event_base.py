# ------------------------------------------------------------------------------
# Test Event Base
# ------------------------------------------------------------------------------
from django.test import TestCase
from ls.joyous.models import (
    removeContentPanels,
    SimpleEventPage,
    MultidayEventPage,
    RecurringEventPage,
    MultidayRecurringEventPage,
    PostponementPage,
    RescheduleMultidayEventPage,
)
from ls.joyous.utils.panels import get_panel_fields


# ------------------------------------------------------------------------------
class Test(TestCase):
    def testRemoveContentPanels(self):
        removeContentPanels(["tz", "location"])
        removeContentPanels("website")
        removed = ("tz", "location", "website")

        for cls in (
            SimpleEventPage,
            MultidayEventPage,
            RecurringEventPage,
            MultidayRecurringEventPage,
            PostponementPage,
            RescheduleMultidayEventPage,
        ):
            with self.subTest(classname=cls.__name__):
                self.assertFalse(
                    any(
                        field in removed
                        for panel in cls.content_panels
                        for field in get_panel_fields(panel)
                    )
                )


# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
# ------------------------------------------------------------------------------
