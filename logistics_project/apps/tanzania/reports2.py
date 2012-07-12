from datetime import datetime, timedelta

from django.utils.functional import curry
from django.utils.translation import ugettext as _
from django.db.models.query_utils import Q

from rapidsms.contrib.locations.models import Location

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

        soh_data = GroupData.objects.exclude(Q(label=SupplyPointStatusValues.REMINDER_SENT) | Q(label=SupplyPointStatusValues.ALERT_SENT))\
                                    .filter(group_summary__title='soh_fac',group_summary__org_summary=org_summary)
        rr_data = GroupData.objects.exclude(Q(label=SupplyPointStatusValues.REMINDER_SENT) | Q(label=SupplyPointStatusValues.ALERT_SENT))\
                                    .filter(group_summary__title='rr_fac',group_summary__org_summary=org_summary)
        delivery_data = GroupData.objects.exclude(Q(label=SupplyPointStatusValues.REMINDER_SENT) | Q(label=SupplyPointStatusValues.ALERT_SENT))\
                                    .filter(group_summary__title='del_fac',group_summary__org_summary=org_summary)
        supervision_data = GroupData.objects.exclude(Q(label=SupplyPointStatusValues.REMINDER_SENT) | Q(label=SupplyPointStatusValues.ALERT_SENT))\
                                    .filter(group_summary__title='super_fac',group_summary__org_summary=org_summary)
        
        dg = DeliveryGroups(month=self.month)

        submitting_group = dg.current_submitting_group(month=self.month)
        processing_group = dg.current_processing_group(month=self.month)
        delivery_group = dg.current_delivering_group(month=self.month)

        soh_json, soh_numbers = convert_data_to_pie_chart(soh_data, date)
        rr_json, submit_numbers = convert_data_to_pie_chart(rr_data, date)
        delivery_json, delivery_numbers = convert_data_to_pie_chart(delivery_data, date)
        supervision_json, supervision_numbers = convert_data_to_pie_chart(supervision_data, date)

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
        self.soh_numbers = soh_numbers
        self.rr_json = rr_json
        self.submit_numbers = submit_numbers
        self.delivery_json = delivery_json
        self.delivery_numbers = delivery_numbers
        self.supervision_json = supervision_json
        self.supervision_numbers = supervision_numbers
        self.total = total
        self.avg_lead_time = avg_lead_time

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

        if len(supervision_data) > 0:
            self.supervision_response = "%.1f%%" % (supervision_data[0].group_summary.historical_responses / supervision_data[0].group_summary.groupdata_set.exclude(Q(label=SupplyPointStatusValues.REMINDER_SENT) | Q(label=SupplyPointStatusValues.ALERT_SENT)).count())
        else:
            self.supervision_response = "<span class='no_data'>None</span>"
        if len(rr_data) > 0:
            self.randr_response = "%.1f%%" % (rr_data[0].group_summary.historical_responses / rr_data[0].group_summary.groupdata_set.exclude(Q(label=SupplyPointStatusValues.REMINDER_SENT) | Q(label=SupplyPointStatusValues.ALERT_SENT)).count())
        else:
            self.randr_response = "<span class='no_data'>None</span>"

        self._submission_chart = None
        # self.dg = DeliveryGroups(month=month, facs=self.facilities)

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

    percent_supervision_received = curry(_percent, fn='supervision_received', of='submitting')
    percent_supervision_not_received = curry(_percent, fn='supervision_not_received', of='submitting')
    percent_supervision_reminder_sent = curry(_percent, fn='supervision_reminder_sent', of='submitting')
    percent_supervision_not_responding = curry(_percent, fn='supervision_not_responding', of='submitting')


    @property
    def stockouts_in_month(self):
        # NOTE: Uses the report month/year, not the current month/year.
        return [f for f in self.facilities if ProductReport.objects.filter(supply_point__pk=f.pk, quantity=0, report_date__month=self.report_month, report_date__year=self.report_year).count()]

    percent_stockouts_in_month = curry(_percent, fn='stockouts_in_month')

    def stocked_out_of(self, product=None, month=None, year=None):
        return [f for f in self.facilities if f.historical_stock(product, year, month, default_value=None) == 0]

    def percent_stocked_out(self, product, year, month):
        return format_percent(len(self.stocked_out_of(product=product, year=year, month=month)), len(self.facilities))
    
    def percent_stocked_out2(self, year, month):
        ret = {}
        ps = ProductAvailabilityData.objects.filter(organization=self.supply_point, date=datetime(year,month,1))
        for p in ps:
            ret[p.product] = format_percent(p.without_stock,p.total)
        return ret

    def supervision_response_rate(self):
        return self.supervision_response

    def randr_response_rate(self):
        return self.randr_response

    def submission_chart(self):
        on_time = len(self.submitted_on_time)
        late = len(self.submitted_late)
        not_submitted = len(self.not_submitted)
        not_responding = len(self.submit_not_responding)

        graph_data = [
                {"display": _("Submitted On Time"),
                 "value": on_time,
                 "color": Colors.GREEN,
                 "description": "(%s) Submitted On Time (%s %s)" % \
                    (on_time, month_name[self.report_month], self.report_year)
                },
                {"display": _("Submitted Late"),
                 "value": late,
                 "color": "orange",
                 "description": "(%s) Submitted Late (%s %s)" % \
                    (late, month_name[self.report_month], self.report_year)
                },
                {"display": _("Haven't Submitted"),
                 "value": not_submitted,
                 "color": Colors.RED,
                 "description": "(%s) Haven't Submitted (%s %s)" % \
                    (not_submitted, month_name[self.report_month], self.report_year)
                },
                {"display": _("Didn't Respond"),
                 "value": not_responding,
                 "color": Colors.PURPLE,
                 "description": "(%s) Didn't Respond (%s %s)" % \
                    (not_responding, month_name[self.report_month], self.report_year)
                }
            ]
        self._submission_chart = PieChartData(_("R&R Submission Summary") + " (%s %s)" % (month_name[self.report_month], self.report_year), graph_data)
        return self._submission_chart

    def delivery_chart(self):
        received = len(self.delivery_received)
        not_received = len(self.delivery_not_received)
        not_responding = len(self.delivery_not_responding)

        graph_data = [
                {"display": _("Delivery Received"),
                 "value": received,
                 "color": Colors.GREEN,
                 "description": "(%s) Delivery Received (%s %s)" % \
                    (received, month_name[self.report_month], self.report_year)
                },
                {"display": _("Delivery Not Received"),
                 "value": not_received,
                 "color": Colors.RED,
                 "description": "(%s) Delivery Not Received (%s %s)" % \
                    (not_received, month_name[self.report_month], self.report_year)
                },
                {"display": _("Didn't Respond"),
                 "value": not_responding,
                 "color": Colors.PURPLE,
                 "description": "(%s) Didn't Respond (%s %s)" % \
                    (not_responding, month_name[self.report_month], self.report_year)
                }
            ]
        self._delivery_chart = PieChartData(_("Delivery Summary") + " (%s %s)" % (month_name[self.report_month], self.report_year), graph_data)
        return self._delivery_chart

    def soh_chart(self):
        on_time = len(self.soh_on_time)
        late = len(self.soh_late)
        not_responding = len(self.soh_not_responding)

        graph_data = [
                {"display": _("Stock Report On Time"),
                 "value": on_time,
                 "color": Colors.GREEN,
                 "description": "(%s) SOH On Time (%s %s)" % \
                    (on_time, month_name[self.report_month], self.report_year)
                },
                {"display": _("Stock Report Late"),
                 "value": late,
                 "color": "orange",
                 "description": "(%s) Submitted Late (%s %s)" % \
                    (late, month_name[self.report_month], self.report_year)
                },
                {"display": _("SOH Not Responding"),
                 "value": not_responding,
                 "color": Colors.PURPLE,
                 "description": "(%s) Didn't Respond (%s %s)" % \
                    (not_responding, month_name[self.report_month], self.report_year)
                }
            ]
        self._soh_chart = PieChartData(_("SOH Submission Summary") + " (%s %s)" % (month_name[self.report_month], self.report_year), graph_data)
        return self._soh_chart

    def supervision_chart(self):
        received = len(self.supervision_received)
        not_received = len(self.supervision_not_received)
        not_responding = len(self.supervision_not_responding)

        graph_data = [
                {"display": _("Supervision Received"),
                 "value": received,
                 "color": Colors.GREEN,
                 "description": "(%s) Supervision Received (%s %s)" % \
                    (received, month_name[self.report_month], self.report_year)
                },
                {"display": _("Supervision Not Received"),
                 "value": not_received,
                 "color": Colors.RED,
                 "description": "(%s) Supervision Not Received (%s %s)" % \
                    (not_received, month_name[self.report_month], self.report_year)
                },
                {"display": _("Supervision Not Responding"),
                 "value": not_responding,
                 "color": Colors.PURPLE,
                 "description": "(%s) Didn't Respond (%s %s)" % \
                    (not_responding, month_name[self.report_month], self.report_year)
                }
            ]
        self._soh_chart = PieChartData(_("Supervision Summary") + " (%s %s)" % (month_name[self.report_month], self.report_year), graph_data)
        return self._soh_chart

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