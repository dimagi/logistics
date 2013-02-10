from django.conf import settings
from django.db.models.query_utils import Q
from django.template.context import RequestContext
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse

from rapidsms.contrib.messagelog.models import Message
from rapidsms.contrib.locations.models import Location

from logistics.decorators import place_in_request
from logistics.models import Product
from logistics.views import MonthPager

from logistics_project.apps.tanzania.reports2 import SupplyPointStatusBreakdown, national_aggregate, location_aggregates
from logistics_project.apps.tanzania.tables import SupervisionTable, RandRReportingHistoryTable,\
    AggregateRandRTable, AggregateStockoutPercentColumn, AggregateSOHTable,\
    AggregateSupervisionTable, AggregateDeliveryTable, DeliveryStatusTable2,\
    UnrecognizedMessagesTable
from logistics_project.apps.tanzania.models import NoDataError, DeliveryGroups

from logistics_project.apps.tanzania.utils import randr_on_time_reporting,\
    supply_points_below
from logistics_project.apps.tanzania.reporting.models import ProductAvailabilityData,\
    ProductAvailabilityDashboardChart
from logistics_project.apps.tanzania.views import convert_product_data_to_sideways_chart,\
    get_facilities_and_location, _generate_soh_tables

class TanzaniaReport(object):
    """
    Framework object for an ILSGateway report.
    """
    slug = "foo"
    name = "bar"
    def __init__(self, request, base_context={}):
        self.request = request
        self.base_context = base_context

    def shared_context(self):
        # Stuff common to all the reports.
        # This should always be available even if the data isn't 
        # found
        self.context = self.base_context.copy()
        self.mp = MonthPager(self.request)
        org = self.request.GET.get('place')
        if not org:
            if self.request.user.get_profile() is not None:
                if self.request.user.get_profile().location is not None:
                    org = self.request.user.get_profile().location.code
                elif self.request.user.get_profile().supply_point is not None:
                    org = self.request.user.get_profile().supply_point.code
        if not org:
            # TODO: Get this from config
            org = 'MOHSW-MOHSW'
        
        self.organization_code = org
        self.location = Location.objects.get(code=org)
        # hack to get around 1.3 brokenness
        report_list = [{"name": r.name, "slug": r.slug} for r in REPORT_LIST] 
        self.context.update({
            "month_pager": self.mp,
            "location": self.location,
            "level": self.level,
            "report_list": report_list,
            "slug": self.slug,
            "name": self.name,
            "destination_url": reverse('new_reports', args=(self.slug,)),
            "nav_mode": "direct-param",
        })

        
    def reset_context(self):
        self.shared_context()
        org = self.organization_code
        self.facs, self.location = get_facilities_and_location(self.request)
        self.dg = DeliveryGroups(self.mp.month, facs=self.facs)
        mp = self.mp

        self.bd = SupplyPointStatusBreakdown(location=self.location, year=self.mp.year, month=self.mp.month)

        product_availability = ProductAvailabilityData.objects.filter(date__range=(mp.begin_date,mp.end_date), supply_point__code=org).order_by('product__sms_code')
        product_dashboard = ProductAvailabilityDashboardChart()
        product_json, product_codes, bar_data = convert_product_data_to_sideways_chart(product_availability, product_dashboard)
        
        self.context.update({
            
            "submitting_group": self.bd.submitting_group,
            "soh_json": self.bd.soh_json,
            "rr_json": self.bd.rr_json,
            "delivery_json": self.bd.delivery_json,
            "supervision_json": self.bd.supervision_json,
            "dg": self.dg,
            # "graph_width": 300, # used in pie_reporting_generic
            # "graph_height": 300,

            "chart_info": product_dashboard,
            "bar_data": bar_data,
            "product_json": product_json,
            "product_codes": product_codes,
            "total": self.bd.total,
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
        if self.level == 'district':
            return "%s/%s-%s.html" % (getattr(settings, 'REPORT_FOLDER'), self.slug, self.level)
        return "%s/%s2.html" % (getattr(settings, 'REPORT_FOLDER'), self.slug)        

    def as_view(self):
        try:
            self.reset_context()
            self.common_report()
        except NoDataError:
            return render_to_response("%s/no_data.html" % getattr(settings, 'REPORT_FOLDER'), 
                                      self.context, context_instance=RequestContext(self.request))
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
        self.context['randr_table'] = AggregateRandRTable\
            (object_list=national_aggregate(month=self.mp.month, year=self.mp.year), 
             request=self.request, month=self.mp.month, year=self.mp.year)

    def regional_report(self):
        self.context['randr_table'] = AggregateRandRTable\
            (object_list=location_aggregates(self.location, month=self.mp.month, year=self.mp.year), 
             request=self.request, month=self.mp.month, year=self.mp.year)

    def district_report(self):
        self.context["on_time"] = randr_on_time_reporting(self.dg.submitting(), self.mp.year, self.mp.month)
        
        self.context["randr_history_table"] = RandRReportingHistoryTable\
            (object_list=self.dg.submitting().select_related(), 
             request=self.request, month=self.mp.month, year=self.mp.year, 
             prefix="randr_history")


class SOHReport(TanzaniaReport):
    name = "Stock On Hand"
    slug = "soh"

    def common_report(self):
        self.context['max_products'] = 6
    
    def national_report(self):
        table = AggregateSOHTable(object_list=national_aggregate(month=self.mp.month, year=self.mp.year), request=self.request, month=self.mp.month, year=self.mp.year)
        products = Product.objects.all().order_by('sms_code')
        for p in products:
            pc = AggregateStockoutPercentColumn(p, self.mp.month, self.mp.year)
            table.add_column(pc, "pc_"+p.sms_code)            
        self.context['soh_table'] = table

    def regional_report(self):
        table = AggregateSOHTable(object_list=location_aggregates(self.location, month=self.mp.month, year=self.mp.year), request=self.request, month=self.mp.month, year=self.mp.year)
        products = Product.objects.all().order_by('sms_code')
        for p in products:
            pc = AggregateStockoutPercentColumn(p, self.mp.month, self.mp.year)
            table.add_column(pc, "pc_"+p.sms_code)            
        self.context['soh_table'] = table

    def district_report(self):
        # NOTE: these might be slow, have not been touched from the old
        # way of doing things
        tables, products, product_set, show = _generate_soh_tables(self.request, self.facs, self.mp)
        self.context.update({
            'tables': tables,
            'products': products,
            'product_set': product_set,
            'show': show,
            'district': True,
        })
        self.context['soh_table'] = tables[0]



class SupervisionReport(TanzaniaReport):
    name = "Supervision"
    slug = "supervision"

    def national_report(self):
        self.context['supervision_table'] = AggregateSupervisionTable(object_list=national_aggregate(month=self.mp.month, year=self.mp.year), request=self.request, month=self.mp.month, year=self.mp.year)

    def regional_report(self):
        self.context['supervision_table'] = AggregateSupervisionTable(object_list=location_aggregates(self.location, month=self.mp.month, year=self.mp.year), request=self.request, month=self.mp.month, year=self.mp.year)

    # def district_report(self):
    #     self.context['supervision_table'] = AggregateSupervisionTable(object_list=location_aggregates(self.location, month=self.mp.month, year=self.mp.year), request=self.request, month=self.mp.month, year=self.mp.year)

    def district_report(self):
        self.context["supervision_table"] = SupervisionTable(object_list=self.dg.total(), request=self.request,
                                            month=self.mp.month, year=self.mp.year, prefix="supervision")

class DeliveryReport(TanzaniaReport):
    name = "Delivery"
    slug = "delivery"

    def national_report(self):
        self.context['delivery_table'] = AggregateDeliveryTable(object_list=national_aggregate(month=self.mp.month, year=self.mp.year), request=self.request, month=self.mp.month, year=self.mp.year)

    def regional_report(self):
        self.context['delivery_table'] = AggregateDeliveryTable(object_list=location_aggregates(self.location, month=self.mp.month, year=self.mp.year), request=self.request, month=self.mp.month, year=self.mp.year)

    def district_report(self):
        self.context["delivery_table"] = DeliveryStatusTable2(object_list=self.dg.delivering().select_related(), request=self.request, month=self.mp.month, year=self.mp.year)

    # def district_report(self):
    #     self.context["delivery_table"] = DeliveryStatusTable(object_list=location_aggregates(self.location, month=self.mp.month, year=self.mp.year), self.dg.delivering().select_related(), request=self.request, month=self.mp.month, year=self.mp.year)


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
