from __future__ import absolute_import

import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _

from alerts.models import NotificationType, Notification
from logistics.const import Reports
from logistics.models import SupplyPoint, LogisticsProfile

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


def missing_report_notifications():
    "Generate notifications when faciltities have not reported"

    enddate = now()
    if isinstance(CONTINUOUS_ERROR_WINDOW, datetime.timedelta):
        offset = CONTINUOUS_ERROR_WINDOW
    else:
        offset = datetime.timedelta(weeks=CONTINUOUS_ERROR_WINDOW)
    startdate = enddate - offset

    # Get facilities which have and haven't reported in the window
    reporting = SupplyPoint.objects.filter(last_reported__gte=startdate, active=True)
    non_reporting = SupplyPoint.objects.filter(
        Q(last_reported=None) | Q(last_reported__lt=startdate), active=True)

    def _generate_uid(point):
        """
        Create a unique notification identifier for this supply point.

        Use year/week portion of the end date and the point pk.
        This mean the noficitaion will not be generated more than once a week.
        """
        year, week, weekday = enddate.isocalendar()
        return u'non-reporting-{pk}-{year}-{week}'.format(pk=point.pk, year=year, week=week)

    # If previously non-reporting for this window then resolve the notification
    uids_to_remove = map(_generate_uid, reporting)
    Notification.objects.filter(uid__in=uids_to_remove).update(is_open=False)

    def _generate_nofitication_text(point):
        """
        Note that this supply point has not reported in the given window.
        """
        params = {
            'start': statedate.strftime('%d %B %Y'),
            'end': enddate.strftime('%d %B %Y'),
            'name': point.name
        }
        msg = _(u'No supply reports were recieved from %(name)s between %(start)s and %(end)s.')
        return msg % params
   
    alert_type = NotReporting.__module__ + '.' + NotReporting.__name__
    # Create a notification for this point
    # rapidsms-alerts will handle the duplicate uids
    for point in non_reporting:
        uid = _generate_uid(point)
        text = _generate_nofitication_text(point)
        yield Notification(alert_type=alert_type, uid=uid, text=text, originating_location=point.location)


def incomplete_report_notifications():
    "Generate notifications when faciltities have incomplete stock reports."


def stockout_notifications():
    "Generate notifications when faciltities have stockouts."
