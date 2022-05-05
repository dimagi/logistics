from __future__ import unicode_literals
from django.contrib import messages

from rapidsms.contrib.messagelog.models import Message

from logistics.models import SupplyPoint, StockRequest, ProductStock

from logistics_project.apps.malawi.warehouse.models import ProductAvailabilityDataSummary, ReportingRate
from logistics_project.apps.malawi.warehouse import warehouse_view
from logistics_project.apps.malawi.util import get_default_supply_point, \
    hsa_supply_points_below, fmt_or_none
from logistics_project.apps.malawi.warehouse.report_utils import get_hsa_url
from rapidsms.models import Contact
from static.malawi.config import SupplyPointCodes


class View(warehouse_view.DistrictOnlyView):
    
    show_report_nav = False
    
    def custom_context(self, request):

        if request.GET.get('hsa_code'):
            hsa = SupplyPoint.objects.filter(code=request.GET.get('hsa_code'), type__code=SupplyPointCodes.HSA)
            if hsa.count():
                self.slug = 'single-hsa'
                return self.single_hsa_context(request, hsa[0])
            else:
                messages.warning(request, "HSA does not exist or is not active")
        
        table = {
            "id": "all-hsas",
            "is_datatable": True,
            "is_downloadable": True,
            "header": ["Facility", "Name", "Id", "Responsible for these Commodities",\
                "Has Stockouts","Has Emergency Levels","Has Products with adequate supply",\
                "Has Overstocks", "Last Message Date"],
            "data": [],
        }

        sp = SupplyPoint.objects.get(location=request.location)\
            if request.location else get_default_supply_point(request.user)

        hsas = hsa_supply_points_below(sp.location)

        for hsa in hsas:
            try:
                pads = ProductAvailabilityDataSummary.objects.filter(
                    supply_point=hsa,
                    base_level=request.base_level
                ).order_by('-date')[0]
            except IndexError:
                pads = None
            
            pads_vals = [_yes_or_no(v) for v in (pads.any_without_stock, 
                                                 pads.any_emergency_stock,
                                                 pads.any_good_stock, 
                                                 pads.any_over_stock)] \
                        if pads else ["no data"] * 4
            
            try:
                last_message_date = _date_fmt(
                    Message.objects.filter(
                        direction='I', contact__supply_point=hsa, contact__is_active=True,
                    ).order_by('-date').values_list('date', flat=True)[0]
                )
            except IndexError:
                last_message_date = ''

            products_managed = ' '.join([p.sms_code for p in hsa.commodities_stocked()])
            table["data"].append({"url": get_hsa_url(hsa, sp.code),
                                  "data": [hsa.supplied_by.name, hsa.name,
                                           hsa.code, 
                                           products_managed] +
                                           pads_vals +
                                           [last_message_date]})

        table["height"] = min(480, (hsas.count()+1)*30)

        return {
                "table": table,
        }

    def single_hsa_context(self, request, hsa):

        # this will fail hard if misconfigured, which is desirable for now
        contact = Contact.objects.get(supply_point=hsa, is_active=True)
        header_table = {
            "id": "header-table",
            "is_datatable": False,
            "is_downloadable": True,
            "header": ["District", "Facility", "HSA", "Id"],
            "data": [[contact.supply_point.supplied_by.supplied_by.name,\
                contact.supply_point.supplied_by.name, contact.name, contact.supply_point.code]],
        }

        report_table = {
            "id": "hsa-reporting-summary",
            "is_datatable": False,
            "is_downloadable": True,
            "header": ["Month", "On Time", "Late", "Complete"],
            "data": [],
        }
        

        reports = ReportingRate.objects.filter(supply_point=hsa).order_by('-date')[:3]
        for rr in reports:
            report_table["data"].append([rr.date.strftime('%b-%Y'), _yes_or_no(rr.on_time),\
                _yes_or_no(rr.late), _yes_or_no(rr.complete)])

        product_stock_tuples = [(p, ProductStock.objects.get(supply_point=hsa, product=p) \
                                    if ProductStock.objects.filter(supply_point=hsa, product=p).exists() \
                                    else None)
                                 for p in hsa.commodities_stocked().order_by("sms_code")]

        def _to_table_values(ps):
            return [ps.daily_consumption, ps.monthly_consumption, 
                    ps.quantity, fmt_or_none(ps.months_remaining, percent=False), 
                    ps.reorder_amount] \
                    if ps else [None] * 5
        calc_cons = {
            "id": "calc-consumption-stock-levels",
            "is_datatable": False,
            "is_downloadable": True,
            "header": ["Product", "Total Daily Consumption",
                       "Average Monthly Consumption", "Current SOH", "Months of Stock on hand",
                       "Resupply Qty Required"],
            "data": [[p.name] + _to_table_values(ps) for p, ps in product_stock_tuples]
        }

        request_table = {
            "id": "order-response-time",
            "is_datatable": True,
            "is_downloadable": True,
            "header": [
                'pk',
                "Product", "Is Emergency", "Balance", "Amt Requested", "Amt Received", "Requested On",
                "Responded On", "Received On", "Status",
            ],
            "data": [],
        }

        stock_requests = StockRequest.objects.filter(supply_point=hsa).order_by('-requested_on')
        for sr in stock_requests:
            request_table["data"].append([
                sr.pk,
                sr.product.name, _yes_or_no(sr.is_emergency), sr.balance, sr.amount_requested,
                sr.amount_received, _date_fmt(sr.requested_on), _date_fmt(sr.responded_on),
                _date_fmt(sr.received_on), sr.status
            ])

        request_table["height"] = min(480, (stock_requests.count()+1)*30)

        msgs_table = {
            "id": "recent-messages",
            "is_datatable": False,
            "is_downloadable": True,
            "header": ["Date", "Message Text"],
            "data": [],
        }

        msgs = Message.objects.filter(direction='I', contact=contact).order_by('-date')[:10]
        for msg in msgs:
            msgs_table["data"].append([_date_fmt(msg.date), msg.text])

        details_table = {
            "id": "hsa-details",
            "is_datatable": False,
            "is_downloadable": True,
            "header": ["", ""],
            "data": [
                ['Name', hsa.name],
                ['Code', hsa.code],
                ['Phone Number', contact.default_connection.identity if contact.default_connection else 'none'],
                ['Products', ' '.join(c.sms_code for c in hsa.commodities_stocked())],
                ['Facility', hsa.supplied_by.name],
                ['District', hsa.supplied_by.supplied_by.name],
            ],
        }
        return {
                "header_table": header_table,
                "report_table": report_table,
                "calc_cons": calc_cons,
                "request_table": request_table,
                "msgs_table": msgs_table,
                "details_table": details_table,
                "contact": contact,
        }

def _yes_or_no(value):
    if value:
        return 'yes'
    return 'no'

def _date_fmt(date):
    if date:
        return date.strftime('%Y-%m-%d')# %H:%M:%S')
    return ""

