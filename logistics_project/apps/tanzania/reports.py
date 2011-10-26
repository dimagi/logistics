from datetime import datetime, timedelta
from logistics.reports import Colors, PieChartData
from logistics.models import SupplyPoint, ProductReport
from django.utils.functional import curry
from logistics_project.apps.tanzania.models import DeliveryGroups, OnTimeStates
from logistics_project.apps.tanzania.utils import submitted_to_msd, randr_reported_on_time, soh_reported_on_time, facilities_below, historical_response_rate, format_percent
from models import SupplyPointStatusTypes, SupplyPointStatusValues
from django.utils.translation import ugettext as _
from rapidsms.contrib.locations.models import Location
from utils import sps_with_latest_status, avg_past_lead_time
from calendar import month_name

class SupplyPointStatusBreakdown(object):

    def __init__(self, facilities=None, year=None, month=None):
        if not (year and month):
            self.month = datetime.utcnow().month
            self.year = datetime.utcnow().year
        else:
            self.month = month
            self.year = year
        if facilities is None:
            facilities = SupplyPoint.objects.filter(type__code="facility", contact__is_active=True).distinct()
        self.facilities = facilities
        self.report_month = self.month - 1 if self.month > 1 else 12
        self.report_year = self.year if self.report_month < 12 else self.year - 1
        self.dg = DeliveryGroups(month=month, facs=self.facilities)
        self._submission_chart = None

    @property
    def submitted(self):
        return list(sps_with_latest_status(sps=self.dg.submitting(self.facilities),
                                                year=self.year, month=self.month,
                                                status_type=SupplyPointStatusTypes.R_AND_R_FACILITY,
                                                status_value=SupplyPointStatusValues.SUBMITTED))
    @property
    def submitted_on_time(self):
        return filter(lambda sp: randr_reported_on_time(sp, self.year, self.month) == OnTimeStates.ON_TIME, self.submitted)

    @property
    def submitted_late(self):
        return filter(lambda sp: randr_reported_on_time(sp, self.year, self.month) == OnTimeStates.LATE, self.submitted)

    @property
    def not_submitted(self):
        return list(sps_with_latest_status(sps=self.dg.submitting(self.facilities),
                                                 year=self.year, month=self.month,
                                                 status_type=SupplyPointStatusTypes.R_AND_R_FACILITY,
                                                 status_value=SupplyPointStatusValues.NOT_SUBMITTED))

    @property
    def submit_reminder_sent(self):
        return list(sps_with_latest_status(sps=self.dg.submitting(self.facilities),
                                                 year=self.year, month=self.month,
                                                 status_type=SupplyPointStatusTypes.R_AND_R_FACILITY,
                                                 status_value=SupplyPointStatusValues.REMINDER_SENT))
    @property
    def submit_not_responding(self):
        return list(set(self.submit_reminder_sent) - set(self.submitted) - set(self.not_submitted))


    @property
    def no_randr_data(self):
        return list(set(self.dg.submitting(self.facilities)) -
                    set(self.submitted_on_time) -
                    set(self.submitted_late) -
                    set(self.not_submitted) -
                    set(self.submit_not_responding))
    @property
    def delivery_received(self):
        return list(sps_with_latest_status(sps=self.dg.delivering(self.facilities),
                                                 year=self.year, month=self.month,
                                                 status_type=SupplyPointStatusTypes.DELIVERY_FACILITY,
                                                 status_value=SupplyPointStatusValues.RECEIVED))

    @property
    def delivery_not_received(self):
        return list(sps_with_latest_status(sps=self.dg.delivering(self.facilities),
                                                 year=self.year, month=self.month,
                                                 status_type=SupplyPointStatusTypes.DELIVERY_FACILITY,
                                                 status_value=SupplyPointStatusValues.NOT_RECEIVED))


    @property
    def delivery_reminder_sent(self):
        return list(sps_with_latest_status(sps=self.dg.delivering(self.facilities),
                                                 year=self.year, month=self.month,
                                                 status_type=SupplyPointStatusTypes.DELIVERY_FACILITY,
                                                 status_value=SupplyPointStatusValues.REMINDER_SENT))

    @property
    def delivery_not_responding(self):
        return list(set(self.delivery_reminder_sent) - set(self.delivery_received) - set(self.delivery_not_received))


    @property
    def supervision_received(self):
        return list(sps_with_latest_status(sps=self.dg.submitting(self.facilities),
                                                 year=self.year, month=self.month,
                                                 status_type=SupplyPointStatusTypes.SUPERVISION_FACILITY,
                                                 status_value=SupplyPointStatusValues.RECEIVED))

    @property
    def supervision_not_received(self):
        return list(sps_with_latest_status(sps=self.dg.submitting(self.facilities),
                                                 year=self.year, month=self.month,
                                                 status_type=SupplyPointStatusTypes.SUPERVISION_FACILITY,
                                                 status_value=SupplyPointStatusValues.NOT_RECEIVED))

    @property
    def supervision_reminder_sent(self):
        return list(sps_with_latest_status(sps=self.dg.submitting(self.facilities),
                                                 year=self.year, month=self.month,
                                                 status_type=SupplyPointStatusTypes.SUPERVISION_FACILITY,
                                                 status_value=SupplyPointStatusValues.REMINDER_SENT))

    @property
    def supervision_not_responding(self):
        return list(set(self.supervision_reminder_sent) - set(self.supervision_received) - set(self.supervision_not_received))


    @property
    def no_supervision_data(self):
        return list(set(self.dg.submitting(self.facilities)) -
                    set(self.supervision_received) -
                    set(self.supervision_not_received) -
                    set(self.supervision_reminder_sent) -
                    set(self.supervision_not_responding))

    @property
    def not_submitted(self):
        return list(sps_with_latest_status(sps=self.dg.submitting(self.facilities),
                                                 year=self.year, month=self.month,
                                                 status_type=SupplyPointStatusTypes.R_AND_R_FACILITY,
                                                 status_value=SupplyPointStatusValues.NOT_SUBMITTED))

    @property
    def submit_reminder_sent(self):
        return list(sps_with_latest_status(sps=self.dg.submitting(self.facilities),
                                                 year=self.year, month=self.month,
                                                 status_type=SupplyPointStatusTypes.R_AND_R_FACILITY,
                                                 status_value=SupplyPointStatusValues.REMINDER_SENT))
    @property
    def submit_not_responding(self):
        return list(set(self.submit_reminder_sent) - set(self.submitted) - set(self.not_submitted))


    @property
    def soh_submitted(self):
        return list(sps_with_latest_status(sps=self.facilities, year=self.year, month=self.month,
                                                         status_type=SupplyPointStatusTypes.SOH_FACILITY,
                                                         status_value=SupplyPointStatusValues.SUBMITTED))

    @property
    def soh_on_time(self):
        return filter(lambda sp: soh_reported_on_time(sp, self.year, self.month) == OnTimeStates.ON_TIME, self.facilities)

    @property
    def soh_late(self):
        return filter(lambda sp: soh_reported_on_time(sp, self.year, self.month) == OnTimeStates.LATE, self.facilities)

    @property
    def soh_not_responding(self):
        return filter(lambda sp: soh_reported_on_time(sp, self.year, self.month) in (OnTimeStates.NO_DATA, OnTimeStates.INSUFFICIENT_DATA), self.facilities)

    @property
    def avg_lead_time(self):
        if not self.facilities: return "<span class='no_data'>No data</span>"
        sum = timedelta(0)
        count = 0
        for f in self.facilities:
            lt = avg_past_lead_time(f)
            if lt:
                sum += lt
                count += 1
        if not count: return "<span class='no_data'>No data</span>"
        return sum / count

    def _percent(self, fn=None, of=None):
        if not of:
            of= len(self.facilities)
        else:
            of = len(getattr(self.dg, of)(self.facilities))
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
        return [f for f in self.facilities if ProductReport.objects.filter(supply_point__pk=f.pk, quantity=0, report_date__month=self.month, report_date__year=self.year).count()]

    percent_stockouts_in_month = curry(_percent, fn='stockouts_in_month')

    def stocked_out_of(self, product=None, month=None, year=None):
        return [f for f in self.facilities if f.historical_stock(product, year, month, default_value=None) == 0]

    def stocked_out_of(self, product=None, month=None, year=None):
        return [f for f in self.facilities if f.historical_stock(product, year, month, default_value=None) == 0]

    def percent_stocked_out(self, product, year, month):
        # Is this pattern confusing?
        return format_percent(len(self.stocked_out_of(product=product, year=year, month=month)), len(self.facilities))

    def _response_rate(self, type=None):
        num = 0.0
        denom = 0.0
        for f in self.dg.submitting(self.facilities):
            hrr = historical_response_rate(f, type)
            if hrr:
                num += hrr[0]
                denom += 1
        if denom:
            return "%.1f%%" % ((num / denom) * 100.0)
        else:
            return "<span class='no_data'>No Data</span>"

    supervision_response_rate = curry(_response_rate, type=SupplyPointStatusTypes.SUPERVISION_FACILITY)
    randr_response_rate = curry(_response_rate, type=SupplyPointStatusTypes.R_AND_R_FACILITY)



    def submission_chart(self):
        graph_data = [
                {"display": _("Submitted On Time"),
                 "value": len(self.submitted_on_time),
                 "color": Colors.GREEN,
                 "description": "(%s) Submitted On Time (%s %s)" % \
                    (len(self.submitted_on_time), month_name[self.report_month], self.report_year)
                },
                {"display": _("Submitted Late"),
                 "value": len(self.submitted_late),
                 "color": "orange",
                 "description": "(%s) Submitted Late (%s %s)" % \
                    (len(self.submitted_late), month_name[self.report_month], self.report_year)
                },
                {"display": _("Haven't Submitted"),
                 "value": len(self.not_submitted),
                 "color": Colors.RED,
                 "description": "(%s) Haven't Submitted (%s %s)" % \
                    (len(self.not_submitted), month_name[self.report_month], self.report_year)
                },
                {"display": _("Didn't Respond"),
                 "value": len(self.submit_not_responding),
                 "color": Colors.PURPLE,
                 "description": "(%s) Didn't Respond (%s %s)" % \
                    (len(self.submit_not_responding), month_name[self.report_month], self.report_year)
                }
            ]
        self._submission_chart = PieChartData(_("R&R Submission Summary") + " (%s %s)" % (month_name[self.report_month], self.report_year), graph_data)
        return self._submission_chart

    def delivery_chart(self):
        graph_data = [
                {"display": _("Delivery Received"),
                 "value": len(self.delivery_received),
                 "color": Colors.GREEN,
                 "description": "(%s) Delivery Received (%s %s)" % \
                    (len(self.delivery_received), month_name[self.report_month], self.report_year)
                },
                {"display": _("Delivery Not Received"),
                 "value": len(self.delivery_not_received),
                 "color": Colors.RED,
                 "description": "(%s) Delivery Not Received (%s %s)" % \
                    (len(self.delivery_not_received), month_name[self.report_month], self.report_year)
                },
                {"display": _("Didn't Respond"),
                 "value": len(self.delivery_not_responding),
                 "color": Colors.PURPLE,
                 "description": "(%s) Didn't Respond (%s %s)" % \
                    (len(self.delivery_not_responding), month_name[self.report_month], self.report_year)
                }
            ]
        self._delivery_chart = PieChartData(_("Delivery Summary") + " (%s %s)" % (month_name[self.report_month], self.report_year), graph_data)
        return self._delivery_chart

    def soh_chart(self):
        graph_data = [
                {"display": _("Stock Report On Time"),
                 "value": len(self.soh_on_time),
                 "color": Colors.GREEN,
                 "description": "(%s) SOH On Time (%s %s)" % \
                    (len(self.soh_on_time), month_name[self.report_month], self.report_year)
                },
                {"display": _("Stock Report Late"),
                 "value": len(self.soh_late),
                 "color": "orange",
                 "description": "(%s) Submitted Late (%s %s)" % \
                    (len(self.soh_late), month_name[self.report_month], self.report_year)
                },
                {"display": _("SOH Not Responding"),
                 "value": len(self.soh_not_responding),
                 "color": Colors.PURPLE,
                 "description": "(%s) Didn't Respond (%s %s)" % \
                    (len(self.soh_not_responding), month_name[self.report_month], self.report_year)
                }
            ]
        self._soh_chart = PieChartData(_("SOH Submission Summary") + " (%s %s)" % (month_name[self.report_month], self.report_year), graph_data)
        return self._soh_chart

    def supervision_chart(self):
        graph_data = [
                {"display": _("Supervision Received"),
                 "value": len(self.supervision_received),
                 "color": Colors.GREEN,
                 "description": "(%s) Supervision Received (%s %s)" % \
                    (len(self.supervision_received), month_name[self.report_month], self.report_year)
                },
                {"display": _("Supervision Not Received"),
                 "value": len(self.supervision_not_received),
                 "color": Colors.RED,
                 "description": "(%s) Supervision Not Received (%s %s)" % \
                    (len(self.supervision_not_received), month_name[self.report_month], self.report_year)
                },
                {"display": _("Supervision Not Responding"),
                 "value": len(self.supervision_not_responding),
                 "color": Colors.PURPLE,
                 "description": "(%s) Didn't Respond (%s %s)" % \
                    (len(self.supervision_not_responding), month_name[self.report_month], self.report_year)
                }
            ]
        self._soh_chart = PieChartData(_("Supervision Summary") + " (%s %s)" % (month_name[self.report_month], self.report_year), graph_data)
        return self._soh_chart

class LocationAggregate(object):
    def __init__(self, location=None, month=None, year=None, view=None):
        self.location = location
        self.breakdown = SupplyPointStatusBreakdown(facilities=facilities_below(location), month=month, year=year)

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