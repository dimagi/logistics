from datetime import datetime

from django.utils.functional import curry
from django.core.exceptions import ObjectDoesNotExist

from rapidsms.contrib.locations.models import Location

from logistics.models import SupplyPoint, ProductReport
from logistics_project.apps.tanzania.models import DeliveryGroups, \
    SupplyPointStatusTypes
from logistics_project.apps.tanzania.models import NoDataError
from logistics_project.apps.tanzania.reporting.models import OrganizationSummary, \
    GroupSummary, ProductAvailabilityData, OrganizationTree
from logistics_project.apps.tanzania.views import convert_data_to_pie_chart
from logistics_project.apps.tanzania.utils import format_percent
from django.conf import settings


class SupplyPointStatusBreakdown(object):

    def __init__(self, location=None, year=None, month=None, facilities=None, report_type=None):
        facilities = facilities or []
        if not (year and month):
            self.month = datetime.utcnow().month
            self.year = datetime.utcnow().year
        else:
            self.month = month
            self.year = year

        self.report_month = self.month - 1 if self.month > 1 else 12
        self.report_year = self.year if self.report_month < 12 else self.year - 1

        date = datetime(self.year, self.month, 1)

        if location is None:
            location = Location.objects.get(code__iexact=settings.COUNTRY)

        self.supply_point = SupplyPoint.objects.get(location=location)
        self.facilities = facilities

        try:
            self.org_summary = OrganizationSummary.objects.get\
                (date=date, supply_point=self.supply_point)
        except ObjectDoesNotExist:
            raise NoDataError()

        self.total = self.org_summary.total_orgs
        avg_lead_time = self.org_summary.average_lead_time_in_days
        if avg_lead_time:
            self.avg_lead_time = "%.1f" % avg_lead_time
        else:
            self.avg_lead_time = "<span class='no_data'>None</span>"


        # TODO: the list generation stuff is kinda ugly, for compatibility
        # with the old way of doing things
        if report_type == 'SOH' or not report_type:
            self.soh_data = GroupSummary.objects.get(title=SupplyPointStatusTypes.SOH_FACILITY,
                                            org_summary=self.org_summary)
            self.soh_json = convert_data_to_pie_chart(self.soh_data, date)

            self.soh_submitted = [''] * self.soh_data.complete
            self.soh_on_time = [''] * self.soh_data.on_time
            self.soh_late = [''] * self.soh_data.late
            self.soh_not_responding = [''] * self.soh_data.not_responding


        if report_type == 'RandR' or not report_type:
            self.rr_data = GroupSummary.objects.get(title=SupplyPointStatusTypes.R_AND_R_FACILITY,
                                                    org_summary=self.org_summary)
            self.rr_json = convert_data_to_pie_chart(self.rr_data, date)
            self.submitted = [''] * self.rr_data.complete
            self.submitted_on_time = [''] * self.rr_data.on_time
            self.submitted_late = [''] * self.rr_data.late
            self.not_submitted = [''] * self.rr_data.not_submitted
            self.submit_not_responding = [''] * self.rr_data.not_responding
            self.no_randr_data = [''] * (self.rr_data.total \
                                            - self.rr_data.on_time \
                                            - self.rr_data.late \
                                            - self.rr_data.not_responding \
                                            - self.rr_data.not_submitted)
            self.submitting = [''] * self.rr_data.total
            self.submit_reminder_sent = []


        if report_type == 'DEL' or not report_type:
            self.delivery_data = GroupSummary.objects.get(title=SupplyPointStatusTypes.DELIVERY_FACILITY,
                                                 org_summary=self.org_summary)
            self.delivery_json = convert_data_to_pie_chart(self.delivery_data, date)

            self.delivery_received = [''] * self.delivery_data.received
            self.delivery_not_received = [''] * self.delivery_data.not_received
            self.delivery_not_responding = [''] * self.delivery_data.not_responding

            self.delivery_reminder_sent = []


        if report_type == 'SUPER' or not report_type:
            self.supervision_data = GroupSummary.objects.get(title=SupplyPointStatusTypes.SUPERVISION_FACILITY,
                                                    org_summary=self.org_summary)
            self.supervision_json = convert_data_to_pie_chart(self.supervision_data, date)

            self.supervision_received = [''] * self.supervision_data.received
            self.supervision_not_received = [''] * self.supervision_data.not_received
            self.supervision_not_responding = [''] * self.supervision_data.not_responding
            self.no_supervision_data = [''] * (self.supervision_data.total \
                                            - self.supervision_data.received \
                                            - self.supervision_data.not_responding \
                                            - self.supervision_data.not_received)
            self.supervising = [''] * self.supervision_data.total
            self.supervision_reminder_sent = []   

        dg = DeliveryGroups(month=self.month)

        self.submitting_group = dg.current_submitting_group(month=self.month)
        self.processing_group = dg.current_processing_group(month=self.month)
        self.delivery_group = dg.current_delivering_group(month=self.month)

        self._submission_chart = None


    def _percent(self, fn=None, of=None):
        if not of:
            of = len(self.facilities)
        else:
            of = len(getattr(self, of))
        return format_percent(len(getattr(self, fn)), of)

    percent_randr_on_time = curry(_percent, fn='submitted_on_time', of='submitting')
    percent_randr_late = curry(_percent, fn='submitted_late', of='submitting')
    percent_randr_not_submitted = curry(_percent, fn='not_submitted', of='submitting')
    percent_randr_reminder_sent = curry(_percent, fn='submit_reminder_sent', of='submitting')
    percent_randr_not_responding = curry(_percent, fn='submit_not_responding', of='submitting')
    percent_randr_no_data = curry(_percent, fn='no_randr_data', of='submitting')

    percent_soh_on_time = curry(_percent, fn='soh_on_time')
    percent_soh_late = curry(_percent, fn='soh_late')
    percent_soh_not_responding = curry(_percent, fn='soh_not_responding')

    percent_supervision_received = curry(_percent, fn='supervision_received', of='facilities')
    percent_supervision_not_received = curry(_percent, fn='supervision_not_received', of='facilities')
    percent_supervision_reminder_sent = curry(_percent, fn='supervision_reminder_sent', of='facilities')
    percent_supervision_not_responding = curry(_percent, fn='supervision_not_responding', of='facilities')

    def supervision_response_rate(self):
        total_responses = 0
        total_possible = 0
        for g in GroupSummary.objects.filter(org_summary__date__lte=datetime(self.year, self.month, 1),
                            org_summary__supply_point=self.supply_point, title='super_fac'):
            if g:
                total_responses += g.responded
                total_possible += g.total
        if total_possible:
            return "%.1f%%" % (100.0 * total_responses / total_possible)
        return "<span class='no_data'>None</span>"

    def randr_response_rate(self):
        total_responses = 0
        total_possible = 0
        for g in GroupSummary.objects.filter(org_summary__date__lte=datetime(self.year, self.month, 1),
                            org_summary__supply_point=self.supply_point, title='rr_fac'):
            if g:
                total_responses += g.responded
                total_possible += g.total
        if total_possible:
            return "%.1f%%" % (100.0 * total_responses / total_possible)
        return "<span class='no_data'>None</span>"

    def percent_stockouts_in_month(self):
        if self.facilities:
            return "%.1f%%" % (ProductReport.objects.filter(supply_point__in=self.facilities, quantity__lte=0, report_date__month=self.report_month, report_date__year=self.report_year).count()\
                                / len(self.facilities))
        return "<span class='no_data'>None</span>"

    def percent_stocked_out(self, product, year, month):
        ps = ProductAvailabilityData.objects.filter(supply_point=self.supply_point, product=product, date=datetime(year, month, 1))
        if ps:
            return format_percent(ps[0].without_stock, ps[0].total)
        return "<span class='no_data'>None</span>"

class LocationAggregate(object):
    def __init__(self, location=None, month=None, year=None, view=None, report_type=None):
        self.location = location
        facs = []
        if location:
            facs = [s.below for s in OrganizationTree.objects.filter(above__code=location.code, is_facility=True)]
        self.breakdown = SupplyPointStatusBreakdown(
            location=location, month=month, year=year, facilities=facs,
            report_type=report_type)


    def __unicode__(self):
        return "%s" % self.name

    @property
    def name(self):
        return self.location.name

    def url(self):
        pass


def national_aggregate(year=None, month=None, report_type=None):
    location = Location.objects.get(type__name="MOHSW")
    return location_aggregates(location, year=year, month=month, report_type=report_type)


def location_aggregates(location, year=None, month=None, report_type=None):
    return [LocationAggregate(location=l, month=month,
                              year=year, report_type=report_type) \
            for l in location.get_children() \
            if SupplyPoint.objects.filter(location=l).count() > 0]
