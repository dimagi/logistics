from django.template.loader import get_template
from views import get_facilities_and_location, _generate_soh_tables, _is_district, _is_region, _is_national
from logistics.decorators import place_in_request
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from logistics_project.apps.tanzania.reports import SupplyPointStatusBreakdown, national_aggregate, location_aggregates
from logistics_project.apps.tanzania.tables import SupervisionTable, RandRReportingHistoryTable, NotesTable, StockOnHandTable, ProductStockColumn, ProductMonthsOfStockColumn, RandRStatusTable, DeliveryStatusTable, AggregateRandRTable, AggregateSOHTable
from logistics_project.apps.tanzania.utils import chunks, get_user_location, soh_on_time_reporting, latest_status, randr_on_time_reporting, submitted_to_msd
from models import DeliveryGroups
from logistics.views import MonthPager
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.conf import settings

class TanzaniaReport(object):
    """
    Framework object for an ILSGateway report.


    """
    slug = ""
    name = ""
    def __init__(self, request, base_context={}):
        self.request = request
        self.base_context = base_context

    def reset_context(self):
        # Stuff common to all the reports.
        self.context = self.base_context
        self.facs, self.location = get_facilities_and_location(self.request)
        self.mp = MonthPager(self.request)
        self.dg = DeliveryGroups(self.mp.month, facs=self.facs)

        self.context.update({
            "facs": self.facs,
            "month_pager": self.mp,
            "location": self.location,
            "level": self.location.type.name,
            "dg": self.dg,
            "report_list": REPORT_LIST,
            "slug": self.slug,
            "name": self.name,
            "destination_url": reverse('new_reports', args=(self.slug,)),
            "nav_mode": "direct-param",
        })

    def common_report(self):
        # Overridden in new templates.
        pass

    def national_report(self):
        raise NotImplementedError

    def regional_report(self):
        raise NotImplementedError

    def district_report(self):
        raise NotImplementedError
    
    def view_name(self):
        pass

    @property
    def level(self):
        return self.location.type.name.lower()

    def template(self):
        return "%s/%s-%s.html" % (getattr(settings, 'REPORT_FOLDER'), self.slug, self.level)

    def as_view(self):
        self.reset_context()
        self.common_report()
        try:
            if self.level == 'mohsw':
                self.national_report()
            elif self.level == 'region':
                self.regional_report()
            elif self.level == 'district':
                self.district_report()
        except NotImplementedError:
            return render_to_response("%s/unimplemented.html" % getattr(settings, 'REPORT_FOLDER'), self.context, context_instance=RequestContext(self.request))
        return render_to_response(self.template(), self.context, context_instance=RequestContext(self.request))


class RandRReport(TanzaniaReport):
    name = "R&R"
    slug = "randr"

    def national_report(self):
        self.context['randr_table'] = AggregateRandRTable(object_list=national_aggregate(month=self.mp.month, year=self.mp.year), request=self.request)

    def regional_report(self):
        self.context['randr_table'] = AggregateRandRTable(object_list=location_aggregates(self.location, month=self.mp.month, year=self.mp.year), request=self.request)

    def district_report(self):
        self.context["randr_status_table"] = RandRStatusTable(object_list=self.dg.submitting().select_related(), request=self.request, month=self.mp.month, year=self.mp.year)
        self.context["on_time"] = randr_on_time_reporting(self.dg.submitting(), self.mp.year, self.mp.month)
        self.context["randr_history_table"] = RandRReportingHistoryTable(object_list=self.dg.submitting().select_related(), request=self.request,
                                                        month=self.mp.month, year=self.mp.year, prefix="randr_history")


class SOHReport(TanzaniaReport):
    name = "Stock On Hand"
    slug = "soh"

    def common_report(self):
        self.context['bd'] = SupplyPointStatusBreakdown(self.facs, self.mp.year, self.mp.month)

    def national_report(self):
        self.context['soh_table'] = AggregateSOHTable(object_list=national_aggregate(month=self.mp.month, year=self.mp.year), request=self.request)

    def regional_report(self):
        self.context['soh_table'] = AggregateSOHTable(object_list=location_aggregates(self.location, month=self.mp.month, year=self.mp.year), request=self.request)

    def district_report(self):
        tables, products, product_set, show = _generate_soh_tables(self.request, self.facs, self.mp)
        self.context.update({
            'tables': tables,
            'products': products,
            'product_set': product_set,
            'show': show,
        })


class SupervisionReport(TanzaniaReport):
    name = "Supervision"
    slug = "supervision"

    def district_report(self):
        self.context["supervision_table"] = SupervisionTable(object_list=self.dg.submitting().select_related(), request=self.request,
                                            month=self.mp.month, year=self.mp.year, prefix="supervision")

class DeliveryReport(TanzaniaReport):
    name = "Delivery"
    slug = "delivery"

    def district_report(self):
        self.context["delivery_table"] = DeliveryStatusTable(object_list=self.dg.delivering().select_related(), request=self.request, month=self.mp.month, year=self.mp.year)

class LeadTimeReport(TanzaniaReport):
    name = "Lead Time"
    slug = "lead_time"
    pass

REPORT_LIST = [
    SOHReport,
    RandRReport,
    SupervisionReport,
    DeliveryReport,
    LeadTimeReport
]

@place_in_request()
def new_reports(request, slug):
    for r in REPORT_LIST:
        if r.slug == slug:
            ri = r(request)
            return ri.as_view()
    ri = SOHReport(request)
    return ri.as_view()