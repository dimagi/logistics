from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponse
from django.db.models.query_utils import Q
from django.template.loader import get_template
from django.template.context import RequestContext
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse

from rapidsms.contrib.messagelog.models import Message

from logistics.reports import DynamicProductAvailabilitySummaryByFacilitySP
from logistics.decorators import place_in_request
from logistics.models import Product
from logistics.views import MonthPager

from logistics_project.apps.tanzania.reports import SupplyPointStatusBreakdown, national_aggregate, location_aggregates
from logistics_project.apps.tanzania.tables import SupervisionTable, RandRReportingHistoryTable, NotesTable, StockOnHandTable, ProductStockColumn, ProductMonthsOfStockColumn, RandRStatusTable, DeliveryStatusTable, AggregateRandRTable, AggregateSOHTable, AggregateStockoutPercentColumn, AggregateSupervisionTable, AggregateDeliveryTable, UnrecognizedMessagesTable
from logistics_project.apps.tanzania.utils import chunks, get_user_location, soh_on_time_reporting, latest_status, randr_on_time_reporting, submitted_to_msd, facilities_below, supply_points_below

from models import DeliveryGroups
from views import get_facilities_and_location, _generate_soh_tables, _is_district, _is_region, _is_national


class TanzaniaReport(object):
    """
    Framework object for an ILSGateway report.
    """
    slug = "foo"
    name = "bar"
    def __init__(self, request, base_context={}):
        self.request = request
        self.base_context = base_context

    def reset_context(self):
        # Stuff common to all the reports.
        self.context = self.base_context.copy()
        self.mp = MonthPager(self.request)

        self.facs, self.location = get_facilities_and_location(self.request)
        self.dg = DeliveryGroups(self.mp.month, facs=self.facs)
        self.bd = SupplyPointStatusBreakdown(self.facs, self.mp.year, self.mp.month)

        report_list = [{"name": r.name, "slug": r.slug} for r in REPORT_LIST] # hack to get around 1.3 brokenness
        self.context.update({
            "month_pager": self.mp,

            "facs": self.facs,
            "location": self.location,

            "level": self.location.type.name,

            "dg": self.dg,
            "bd": self.bd,

            "report_list": report_list,
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
            elif self.level == 'facility':
                raise NotImplementedError
        except NotImplementedError:
            return render_to_response("%s/unimplemented.html" % getattr(settings, 'REPORT_FOLDER'), self.context, context_instance=RequestContext(self.request))
        return render_to_response(self.template(), self.context, context_instance=RequestContext(self.request))


class RandRReport(TanzaniaReport):
    name = "R&R"
    slug = "randr"
    
    def national_report(self):
        self.context['randr_table'] = AggregateRandRTable(object_list=national_aggregate(month=self.mp.month, year=self.mp.year), request=self.request, month=self.mp.month, year=self.mp.year)

    def regional_report(self):
        self.context['randr_table'] = AggregateRandRTable(object_list=location_aggregates(self.location, month=self.mp.month, year=self.mp.year), request=self.request, month=self.mp.month, year=self.mp.year)

    def district_report(self):
        self.context["on_time"] = randr_on_time_reporting(self.dg.submitting(), self.mp.year, self.mp.month)
        self.context["rr_json"] = self.bd.submission_chart().data
        self.context["randr_history_table"] = RandRReportingHistoryTable(object_list=self.dg.submitting().select_related(), request=self.request,
                                                        month=self.mp.month, year=self.mp.year, prefix="randr_history")


class SOHReport(TanzaniaReport):
    name = "Stock On Hand"
    slug = "soh"

    def common_report(self):
        self.context['max_products'] = 6
        self.context['summary'] = DynamicProductAvailabilitySummaryByFacilitySP(facilities_below(self.location).filter(contact__is_active=True).distinct(), year=self.mp.year, month=self.mp.month)
    
    def national_report(self):
        table = AggregateSOHTable(object_list=national_aggregate(month=self.mp.month, year=self.mp.year), request=self.request, month=self.mp.month, year=self.mp.year)
        products = Product.objects.all().order_by('sms_code')
        for product in products:
            pc = AggregateStockoutPercentColumn(product, self.mp.month, self.mp.year)
            table.add_column(pc, "pc_"+product.sms_code)
        self.context['soh_table'] = table

    def regional_report(self):
        table = AggregateSOHTable(object_list=location_aggregates(self.location, month=self.mp.month, year=self.mp.year), request=self.request, month=self.mp.month, year=self.mp.year)
        products = Product.objects.all().order_by('sms_code')
        for product in products:
            pc = AggregateStockoutPercentColumn(product, self.mp.month, self.mp.year)
            table.add_column(pc, "pc_"+product.sms_code)
        self.context['soh_table'] = table

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

    def national_report(self):
        self.context['supervision_table'] = AggregateSupervisionTable(object_list=national_aggregate(month=self.mp.month, year=self.mp.year), request=self.request, month=self.mp.month, year=self.mp.year)

    def regional_report(self):
        self.context['supervision_table'] = AggregateSupervisionTable(object_list=location_aggregates(self.location, month=self.mp.month, year=self.mp.year), request=self.request, month=self.mp.month, year=self.mp.year)

    def district_report(self):
        self.context['supervision_json'] = self.bd.supervision_chart().data 
        self.context["supervision_table"] = SupervisionTable(object_list=self.dg.submitting().select_related(), request=self.request,
                                            month=self.mp.month, year=self.mp.year, prefix="supervision")

class DeliveryReport(TanzaniaReport):
    name = "Delivery"
    slug = "delivery"

    def national_report(self):
        self.context['delivery_table'] = AggregateDeliveryTable(object_list=national_aggregate(month=self.mp.month, year=self.mp.year), request=self.request, month=self.mp.month, year=self.mp.year)

    def regional_report(self):
        self.context['delivery_table'] = AggregateDeliveryTable(object_list=location_aggregates(self.location, month=self.mp.month, year=self.mp.year), request=self.request, month=self.mp.month, year=self.mp.year)

    def district_report(self):
        self.context['delivery_json'] = self.bd.delivery_chart().data 
        self.context["delivery_table"] = DeliveryStatusTable(object_list=self.dg.delivering().select_related(), request=self.request, month=self.mp.month, year=self.mp.year)


class UnrecognizedMessagesReport(TanzaniaReport):
    name = "Unrecognized SMS"
    slug = "unrecognized"

    def national_report(self):
        self.context['table'] = UnrecognizedMessagesTable(request=self.request, object_list=Message.objects.exclude(contact=None).filter(date__month=self.mp.month,
                                                                                                                   date__year=self.mp.year).filter(Q(tags__name__in=["Handler_DefaultHandler"]) | Q(tags__name__in=["Error"])))
    def regional_report(self):
        self.context['table'] = UnrecognizedMessagesTable(request=self.request, object_list=Message.objects.exclude(contact=None).filter(contact__supply_point__in=supply_points_below(self.location), date__month=self.mp.month,
                                                                                                                   date__year=self.mp.year).filter(Q(tags__name__in=["Handler_DefaultHandler"]) | Q(tags__name__in=["Error"])))
    def district_report(self):
        self.context['table'] = UnrecognizedMessagesTable(request=self.request, object_list=Message.objects.exclude(contact=None).filter(contact__supply_point__in=supply_points_below(self.location), date__month=self.mp.month,
                                                                                                                   date__year=self.mp.year).filter(Q(tags__name__in=["Handler_DefaultHandler"]) | Q(tags__name__in=["Error"])))

REPORT_LIST = [
    SOHReport,
    RandRReport,
    SupervisionReport,
    DeliveryReport,
    UnrecognizedMessagesReport
]

@place_in_request()
def new_reports(request, slug=None):
    for r in REPORT_LIST:
        if r.slug == slug:
            ri = r(request)
            return ri.as_view()
    ri = REPORT_LIST[0](request)
    return ri.as_view()
