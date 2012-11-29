from __future__ import absolute_import

import collections
import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q, F, Max
from django.utils.translation import ugettext_lazy as _

from alerts.models import NotificationType, Notification
from logistics.const import Reports
from logistics.models import SupplyPoint, LogisticsProfile, ProductReport, Product
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


class UrgentStockout(OwnerNotificationType):
    "A number of facilities in a region/country have a stockout."


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
        if profile.program:
            facilities = profile.location.all_facilities()
            missing = []
            facility_products = {}
            reports = ProductReport.objects.filter(product__type=profile.program,
                report_type__code=Reports.SOH, supply_point__in=facilities,
                report_date__lte=self.enddate,
            ).values(
                'supply_point', 'product',
            ).annotate(last_reported=Max('report_date'))

            for report in reports:
                facility_products['%(supply_point)s-%(product)s' % report] = report['last_reported']

            for facility in facilities:
                def _report_missing(product):
                    key = '%s-%s' % (facility.pk, product.pk)
                    last_report = facility_products.get(key, None)
                    return last_report is None or last_report < self.startdate
                products = facility.commodities_stocked().filter(type=profile.program)
                if products and all(map(_report_missing, products)):
                    missing.append(facility)
            return missing
        else:
            return profile.location.all_facilities().filter(
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
        facilities = profile.location.all_facilities()
        incomplete = []
        type_q = Q()
        if profile.program:
            type_q = Q(product__type=profile.program)
        facility_products = {}
        reports = ProductReport.objects.filter(type_q,
            report_type__code=Reports.SOH, supply_point__in=facilities,
            report_date__gte=self.startdate, report_date__lte=self.enddate,
        )
        for report in reports:
            products = facility_products.get(report.supply_point, set([]))
            products.add(report.product)
            facility_products[report.supply_point] = products
        for supply_point, reported in facility_products.items():
            expected = supply_point.commodities_stocked()
            if profile.program:
                expected = expected.filter(type=profile.program)
            expected = set(list(expected))
            if expected - reported:
                incomplete.append(supply_point)
        return incomplete

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


class StockoutNotification(DistrictUserNotification):
    "Generate notifications when faciltities have stockouts."

    notification_type = Stockout

    def get_facilities(self, profile):
        """
        Return the set of facilities have stockouts for the period.
        """
        facilities = profile.location.all_facilities()
        type_q = Q()
        if profile.program:
            type_q = Q(product__type=profile.program)
        results = []
        # Requires product is stocked out for the entire period
        stockouts = ProductReport.objects.filter(type_q,
            report_type__code=Reports.SOH, supply_point__in=facilities,
            report_date__gte=self.startdate, report_date__lte=self.enddate,
        ).values(
            'supply_point', 'product'
        ).annotate(max_quantity=Max('quantity'))
        results = set([so['supply_point'] for so in stockouts if so['max_quantity'] == 0])
        return SupplyPoint.objects.filter(pk__in=results)

    def _generate_uid(self, profile):
        """
        Use year/week portion of the end date and the point pk.
        This mean the noficitaion will not be generated more than once a week.
        """
        year, week, weekday = self.enddate.isocalendar()
        return u'stockout-{pk}-{year}-{week}'.format(pk=profile.pk, year=year, week=week)

    def _generate_nofitication_text(self, profile, matches):
        params = {
            'count': CONTINUOUS_ERROR_WEEKS,
            'names': u', '.join([m.name for m in matches]),
        }
        msg = _(u'These facilities experienced stockouts for the past %(count)s weeks! Please follow up: %(names)s')
        return msg % params


stockout_notifications = StockoutNotification()


def urgent_stockout_notifications():
    "Monthly SMS notifications for stockouts of more than 50% of the facilities."
    profiles = LogisticsProfile.objects.filter(
        location__code__in=(config.LocationCodes.COUNTRY, config.LocationCodes.REGION, )
    ).select_related('location')
    today = now()
    for profile in profiles:
        facilities = profile.location.all_facilities()
        product_info = collections.defaultdict(lambda: {'expected': 0, 'missing': 0})
        # For all products, check if there are stockouts for 50% or more of
        # of the facilities
        for facility in facilities:
            for stock in facility.productstock_set.filter(is_active=True):
                product_info[stock.product]['expected'] += 1
                if stock.quantity == 0:
                    product_info[stock.product]['missing'] += 1
        critcal = filter(lambda p: product_info[p]['missing'] > product_info[p]['expected'] / 2.0, product_info)
        if critcal:
            params = {
                'location': profile.location.name,
                'names': u', '.join([p.name for p in critcal]),
            }
            msg = _(u'URGENT STOCKOUT: >50%% of the facilities in %(location)s are experiencing stockouts of: %(names)s')
            text = msg % params
            alert_type = UrgentStockout.__module__ + '.' + UrgentStockout.__name__
            uid = u'urguent-stockout-{pk}-{year}-{month}'.format(pk=profile.pk, year=today.year, month=today.month)
            yield Notification(alert_type=alert_type, uid=uid, text=text, owner=profile.user)


def sms_notifications(sender, instance, created, **kwargs):
    """
    Post-save handler for NotificationVisibility to send an SMS
    when the notification is created.
    """
    if created:
        notification = instance.notif
        profile = instance.user.get_profile()
        if profile.sms_notifications and profile.contact:
            connection = profile.contact.default_connection
            if connection:
                send_message(connection, notification.text)
