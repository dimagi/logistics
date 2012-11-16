from __future__ import absolute_import

import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q, F
from django.utils.translation import ugettext_lazy as _

from alerts.models import NotificationType, Notification
from logistics.const import Reports
from logistics.models import SupplyPoint, LogisticsProfile, ProductReport
from logistics.util import config

from .compat import now, send_message


CONTINUOUS_ERROR_WEEKS = getattr(settings, 'NOTIFICATION_ERROR_WEEKS', 2)


class OwnerNotificationType(NotificationType):
    """
    Notification type which has no escalation levels and instead creates
    notifications based on the notification owner.
    """

    escalation_levels = ('owner', )

    def users_for_escalation_level(self, esc_level):
        # NotificationType hijacks attribute lookups and passes them
        # on to the underlying notification
        return (self.owner, )

    def auto_escalation_interval(self, esc_level):
        return None

    def escalation_level_name(self, esc_level):
        return 'owner'


class NotReporting(OwnerNotificationType):
    "Facilities have not reported recently."


class IncompelteReporting(OwnerNotificationType):
    "Facilities have submitted incomplete stock report."


class Stockout(OwnerNotificationType):
    "Facilities have a stockout."


class UserFacilitiesNotification(object):
    """
    Base class for creating user notificatoins based on the facilities they are
    interested in or overseeing.
    """

    notification_type = None

    def __init__(self):
        self.startdate, self.enddate = None, None

    def __call__(self):
        "Generate notifcations."
        self.enddate = now()
        offset = datetime.timedelta(weeks=CONTINUOUS_ERROR_WEEKS)
        self.startdate = self.enddate - offset
        alert_type = self.notification_type.__module__ + '.' + self.notification_type.__name__
        for profile in self.get_profiles():
            uid = self._generate_uid(profile)
            matching_facilities = self.get_facilities(profile)
            if not matching_facilities:
                # Issue has since been resolved
                Notification.objects.filter(
                    alert_type=alert_type, uid=uid
                ).update(is_open=False)
            else:
                text = self._generate_nofitication_text(profile, matching_facilities)
                yield Notification(alert_type=alert_type, uid=uid, text=text, owner=profile.user)

    def get_profiles(self):
        "Return the set of all LogisticsProfiles which may recieve a notification."
        raise NotImplemented("Defined in the subclass")

    def get_facilities(self, profile):
        """
        Return the set of facilities which should get the notifications and
        optionally the set of facilities which did not match.
        (matching, non_matching or None)
        """
        raise NotImplemented("Defined in the subclass")

    def _generate_uid(self, profile):
        """
        Create a unique notification identifier for this user.
        """
        raise NotImplemented("Defined in the subclass")

    def _generate_nofitication_text(self, profile, matches):
        """
        Text for user notification
        """
        raise NotImplemented("Defined in the subclass")


class DistrictUserNotification(UserFacilitiesNotification):
    "Base for generating notifications for district level users."

    def get_profiles(self):
        "Return all users associated with a district location."
        return LogisticsProfile.objects.filter(
            location__code=config.LocationCodes.DISTRICT
        ).select_related('location')


class MissingReportsNotification(DistrictUserNotification):
    "Generate notifications when faciltities have not reported"

    notification_type = NotReporting

    def get_facilities(self, profile):
        "Return the set of facilities which have not reported since the start period."
        return profile.location.all_facilities.filter(
            Q(last_reported__isnull=True) | Q(last_reported__lt=self.startdate)
        )

    def _generate_uid(self, profile):
        """
        Use year/week portion of the end date and the point pk.
        This mean the noficitaion will not be generated more than once a week.
        """
        year, week, weekday = self.enddate.isocalendar()
        return u'non-reporting-{pk}-{year}-{week}'.format(pk=profile.pk, year=year, week=week)

    def _generate_nofitication_text(self, profile, matches):
        """
        Note that this supply point has not reported in the given window.
        """
        params = {
            'count': CONTINUOUS_ERROR_WEEKS,
            'names': u', '.join([m.name for m in matches]),
        }
        msg = _(u'These facilities have not submitted their SMS stock report in %(count)s weeks! Please follow up: %(names)s')
        return msg % params


missing_report_notifications = MissingReportsNotification()


class IncompleteReportsNotification(DistrictUserNotification):
    "Generate notifications when faciltities have incomplete stock reports."

    notification_type = IncompelteReporting

    def get_facilities(self, profile):
        """
        Return the set of facilities which do not have supply reports for all
        products in the time period.
        """
        return []
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

    def _generate_uid(self, profile):
        """
        Use year/week portion of the end date and the point pk.
        This mean the noficitaion will not be generated more than once a week.
        """
        year, week, weekday = self.enddate.isocalendar()
        return u'incomplete-{pk}-{year}-{week}'.format(pk=profile.pk, year=year, week=week)

    def _generate_nofitication_text(self, profile, matches):
        """
        Note that this supply point sent an imcomplete report.
        """
        params = {
            'count': CONTINUOUS_ERROR_WEEKS,
            'names': u', '.join([m.name for m in matches]),
        }
        msg = _(u'These facilities have not submitted complete SMS stock reports in %(count)s weeks! Please follow up: %(names)s')
        return msg % params


incomplete_report_notifications = IncompleteReportsNotification()


def stockout_notifications():
    "Generate notifications when faciltities have stockouts."


def sms_notifications(sender, instance, created, **kwargs):
    """
    Post-save handler for NotificationVisibility to send an SMS
    when the notification is created.
    """
    if created:
        notification = instance.notif
        profile = instance.user.get_profile()
        if profile.contact:
            connection = profile.contact.default_connection
            if connection:
                send_message(connection, notification.text)