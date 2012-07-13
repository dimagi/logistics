from datetime import datetime, timedelta

from django.utils.functional import curry
from django.utils.translation import ugettext as _
from django.db.models.query_utils import Q

from rapidsms.contrib.locations.models import Location

from dimagi.utils.dates import months_between

from logistics.reports import Colors, PieChartData
from logistics.models import SupplyPoint, ProductReport

from logistics_project.apps.tanzania.models import DeliveryGroups, OnTimeStates
from logistics_project.apps.tanzania.utils import submitted_to_msd, randr_reported_on_time, soh_reported_on_time, facilities_below, historical_response_rate, format_percent, sps_with_status

from logistics_project.apps.tanzania.reporting.models import *
from logistics_project.apps.tanzania.views import *
from logistics_project.apps.tanzania.models import NoDataError

from models import SupplyPointStatusTypes, SupplyPointStatusValues
from utils import sps_with_latest_status, avg_past_lead_time
from calendar import month_name
from django.core.exceptions import ObjectDoesNotExist


class SupplyPointStatusBreakdown(object):

    def __init__(self, org=None, year=None, month=None):
        # write to db instead

        if not (year and month):
            self.month = datetime.utcnow().month
            self.year = datetime.utcnow().year
        else:
            self.month = month
            self.year = year

        if org is None:
            org = 'MOHSW-MOHSW'


        location = Location.objects.get(code=org)
        self.facilities=facilities_below(location)
        self.supply_point = SupplyPoint.objects.get(code=org)

        self.report_month = self.month - 1 if self.month > 1 else 12
        self.report_year = self.year if self.report_month < 12 else self.year - 1

        date = datetime(self.year, self.month,1)

        try:
            org_summary = OrganizationSummary.objects.get\
                (date__range=(date,datetime.fromordinal(date.toordinal()+29)),
                 organization__code=org)
        except ObjectDoesNotExist:
            raise NoDataError()

        soh_data = GroupSummary.objects.get(title=SupplyPointStatusTypes.SOH_FACILITY,
                                            org_summary=org_summary)
        rr_data = GroupSummary.objects.get(title=SupplyPointStatusTypes.R_AND_R_FACILITY,
                                           org_summary=org_summary)
        delivery_data = GroupSummary.objects.get(title=SupplyPointStatusTypes.R_AND_R_FACILITY,
                                                 org_summary=org_summary)
        supervision_data = GroupSummary.objects.get(title=SupplyPointStatusTypes.SUPERVISION_FACILITY,
                                                    org_summary=org_summary)
        
        dg = DeliveryGroups(month=self.month)

        submitting_group = dg.current_submitting_group(month=self.month)
        processing_group = dg.current_processing_group(month=self.month)
        delivery_group = dg.current_delivering_group(month=self.month)

        soh_json = convert_data_to_pie_chart(soh_data, date, True)
        rr_json = convert_data_to_pie_chart(rr_data, date, True)
        delivery_json = convert_data_to_pie_chart(delivery_data, date)
        supervision_json = convert_data_to_pie_chart(supervision_data, date)

        total = org_summary.total_orgs
        avg_lead_time = org_summary.average_lead_time_in_days

        self.org_summary = org_summary
        self.soh_data = soh_data
        self.rr_data = rr_data
        self.delivery_data = delivery_data
        self.supervision_data = supervision_data
        self.submitting_group = submitting_group
        self.processing_group = processing_group
        self.delivery_group = delivery_group
        self.soh_json = soh_json
        self.soh_numbers = soh_data
        self.rr_json = rr_json
        self.submit_numbers = rr_data
        self.delivery_json = delivery_json
        self.delivery_numbers = delivery_data
        self.supervision_json = supervision_json
        self.supervision_numbers = supervision_data
        self.total = total
        self.avg_lead_time = avg_lead_time

        # TODO: this will break
        self.submitted = [''] * submit_numbers['complete']
        self.submitted_on_time = [''] * submit_numbers['on_time']
        self.submitted_late = [''] * submit_numbers['late']
        self.not_submitted = [''] * submit_numbers['not_submitted']
        self.submit_not_responding = [''] * submit_numbers['not_responding']
        self.no_randr_data = [''] * (submit_numbers['total'] \
                                        - submit_numbers['on_time'] \
                                        - submit_numbers['late'] \
                                        - submit_numbers['not_responding'] \
                                        - submit_numbers['not_submitted'])
        self.submitting = [''] * submit_numbers['total']

        self.submit_reminder_sent = []

        self.delivery_received = [''] * delivery_numbers['received']
        self.delivery_not_received = [''] * delivery_numbers['not_received']
        self.delivery_not_responding = [''] * delivery_numbers['not_responding']

        self.delivery_reminder_sent = []

        self.supervision_received = [''] * supervision_numbers['received']
        self.supervision_not_received = [''] * supervision_numbers['not_received']
        self.supervision_not_responding = [''] * supervision_numbers['not_responding']
        self.no_supervision_data = [''] * (supervision_numbers['total'] \
                                        - supervision_numbers['received'] \
                                        - supervision_numbers['not_responding'] \
                                        - supervision_numbers['not_received'])
        self.supervising = [''] * supervision_numbers['total']
        self.supervision_reminder_sent = []

        self.soh_submitted = [''] * soh_numbers['complete']
        self.soh_on_time = [''] * soh_numbers['on_time']
        self.soh_late = [''] * soh_numbers['late']
        self.soh_not_responding = [''] * soh_numbers['not_responding']

        if avg_lead_time:
            self.avg_lead_time = avg_lead_time
        else:
            self.avg_lead_time = "<span class='no_data'>None</span>"

        self._submission_chart = None

    def _percent(self, fn=None, of=None):
        if not of:
            of= len(self.facilities)
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
        for year, month in months_between(datetime(self.year-1, self.month, 1),datetime(self.year,self.month,1)):
            g = GroupSummary.objects.filter(org_summary__organization=self.supply_point, org_summary__date=datetime(year,month,1), title='super_fac')
            if g:
                total_responses += g[0].historical_responses
                total_possible += g[0].org_summary.total_orgs
        if total_possible:
            return "%.1f%%" % (100.0 * total_responses / total_possible)
        return "<span class='no_data'>None</span>"

    def randr_response_rate(self):
        total_responses = 0
        total_possible = 0
        for year, month in months_between(datetime(self.year-1, self.month, 1),datetime(self.year,self.month,1)):
            g = GroupSummary.objects.filter(org_summary__organization=self.supply_point, org_summary__date=datetime(year,month,1), title='rr_fac')
            if g:
                total_responses += g[0].historical_responses
                total_possible += g[0].org_summary.total_orgs
        if total_possible:
            return "%.1f%%" % (100.0 * total_responses / total_possible)
        return "<span class='no_data'>None</span>"

    @property
    def stockouts_in_month(self):
        # NOTE: Uses the report month/year, not the current month/year.
        return [f for f in self.facilities if ProductReport.objects.filter(supply_point__pk=f.pk, quantity__lte=0, report_date__month=self.report_month, report_date__year=self.report_year).count()]

    percent_stockouts_in_month = curry(_percent, fn='stockouts_in_month')

    def percent_stocked_out(self, product, year, month):
        ps = ProductAvailabilityData.objects.filter(organization=self.supply_point, product=product, date=datetime(year,month,1))
        if ps:
            return format_percent(ps[0].without_stock,ps[0].total)
        return "<span class='no_data'>None</span>"

class LocationAggregate(object):
    def __init__(self, location=None, month=None, year=None, view=None):
        self.location = location
        self.breakdown = SupplyPointStatusBreakdown(org=location.code, month=month, year=year)

    def __unicode__(self):
        return "%s" % self.name

    @property
    def name(self):
        return self.location.name

    def url(self):
        pass

def national_aggregate(year=None, month=None):
    location = Location.objects.get(type__name="MOHSW")
    return location_aggregates(location, year=year, month=month)

def location_aggregates(location, year=None, month=None):
    return [LocationAggregate(location=x, month=month, year=year) for x in location.get_children()]