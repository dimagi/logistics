from __future__ import absolute_import

import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q, F
from django.utils.translation import ugettext_lazy as _

from alerts.models import NotificationType, Notification
from logistics.const import Reports
from logistics.models import SupplyPoint, LogisticsProfile, ProductReport

# Forward compatible import to work with Django 1.4 timezone support
try:
    from django.utils.timezone import now
except ImportError:
    now = datetime.datetime.now

CONTINUOUS_ERROR_WINDOW = getattr(settings, 'NOTIFICATION_ERROR_WINDOW', 2)


class LocationNotificationType(NotificationType):
    """
    Notification type which has no escalation levels and instead creates
    notifications based on the location associated with the user and
    the notification.
    """

    escalation_levels = ('everyone', )

    def users_for_escalation_level(self, esc_level):
        # NotificationType hijacks attribute lookups and passes them
        # on to the underlying notification
        location = self.originating_location
        return User.objects.filter(logisticsprofile__location=location).distinct()

    def auto_escalation_interval(self, esc_level):
        return None

    def escalation_level_name(self, esc_level):
        return 'everyone'


class NotReporting(LocationNotificationType):
    "Facility has not reported recently."


class IncompelteReporting(LocationNotificationType):
    "Facility has submitted incomplete stock report."


class Stockout(LocationNotificationType):
    "Facility has a stockout."


class FacilityNotification(object):
    "Base class for creating facility related notifications."

    notification_type = None

    def __init__(self):
        self.startdate, self.enddate = None, None

    def __call__(self):
        "Generate notifcations."
        self.enddate = now()
        if isinstance(CONTINUOUS_ERROR_WINDOW, datetime.timedelta):
            offset = CONTINUOUS_ERROR_WINDOW
        else:
            offset = datetime.timedelta(weeks=CONTINUOUS_ERROR_WINDOW)
        self.startdate = self.enddate - offset
        matching_facilities, remaining_facilites = self.get_facilities()
        alert_type = self.notification_type.__module__ + '.' + self.notification_type.__name__
        if remaining_facilites is not None:
            # Resolve matches for previously matched
            uids_to_remove = map(self._generate_uid, remaining_facilites)
            Notification.objects.filter(
                alert_type=alert_type, uid__in=uids_to_remove
            ).update(is_open=False)
        # Create a notification for this point
        # rapidsms-alerts will handle the duplicate uids
        for point in matching_facilities:
            uid = self._generate_uid(point)
            text = self._generate_nofitication_text(point)
            yield Notification(alert_type=alert_type, uid=uid, text=text, originating_location=point.location)

    def get_facilities(self):
        """
        Return the set of facilities which should get the notifications and
        optionally the set of facilities which did not match.
        (matching, non_matching or None)
        """
        raise NotImplemented("Defined in the subclass")

    def _generate_uid(self, point):
        """
        Create a unique notification identifier for this supply point.
        """
        raise NotImplemented("Defined in the subclass")

    def _generate_nofitication_text(self, point):
        """
        Text for user notification
        """
        raise NotImplemented("Defined in the subclass")


class MissingReportsNotification(FacilityNotification):
    "Generate notifications when faciltities have not reported"

    notification_type = NotReporting

    def get_facilities(self):
        "Return the set of facilities which have not reported since the start period."
        matching = SupplyPoint.objects.filter(
            Q(last_reported__isnull=True) | Q(last_reported__lt=self.startdate),
            active=True
        )
        remaining = SupplyPoint.objects.filter(
            last_reported__gte=self.startdate, active=True
        )
        return matching, remaining

    def _generate_uid(self, point):
        """
        Use year/week portion of the end date and the point pk.
        This mean the noficitaion will not be generated more than once a week.
        """
        year, week, weekday = self.enddate.isocalendar()
        return u'non-reporting-{pk}-{year}-{week}'.format(pk=point.pk, year=year, week=week)

    def _generate_nofitication_text(self, point):
        """
        Note that this supply point has not reported in the given window.
        """
        params = {
            'start': self.startdate.strftime('%d %B %Y'),
            'end': self.enddate.strftime('%d %B %Y'),
            'name': point.name
        }
        msg = _(u'No supply reports were recieved from %(name)s between %(start)s and %(end)s.')
        return msg % params


missing_report_notifications = MissingReportsNotification()


class IncompleteReportsNotification(FacilityNotification):
    "Generate notifications when faciltities have incomplete stock reports."

    notification_type = IncompelteReporting

    def get_facilities(self):
        """
        Return the set of facilities which do not have supply reports for all
        products in the time period.
        """
        complete = []
        incomplete = []
        facility_products = {}
        reports = ProductReport.objects.filter(
            report_type__code=Reports.SOH, supply_point__active=True,
            report_date__gte=self.startdate, report_date__lte=self.enddate,
        )
        for report in reports:
            products = facility_products.get(report.supply_point, set([]))
            products.add(report.product)
            facility_products[report.supply_point] = products
        for supply_point, reported in facility_products.items():
            expected = set(list(supply_point.commodities_stocked()))
            if expected - reported:
                incomplete.append(supply_point)
            else:
                complete.append(supply_point)
        return incomplete, complete

    def _generate_uid(self, point):
        """
        Use year/week portion of the end date and the point pk.
        This mean the noficitaion will not be generated more than once a week.
        """
        year, week, weekday = self.enddate.isocalendar()
        return u'incomplete-{pk}-{year}-{week}'.format(pk=point.pk, year=year, week=week)

    def _generate_nofitication_text(self, point):
        """
        Note that this supply point sent an imcomplete report.
        """
        params = {
            'start': self.startdate.strftime('%d %B %Y'),
            'end': self.enddate.strftime('%d %B %Y'),
            'name': point.name
        }
        msg = _(u'Incomplete stock reports were recieved from %(name)s between %(start)s and %(end)s.')
        return msg % params


incomplete_report_notifications = IncompleteReportsNotification()


def stockout_notifications():
    "Generate notifications when faciltities have stockouts."
