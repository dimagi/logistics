from django.contrib import messages

from rapidsms.contrib.messagelog.models import Message

from logistics.models import SupplyPoint, Product, StockRequest

from logistics_project.apps.malawi.warehouse.models import UserProfileData,\
    ProductAvailabilityDataSummary, ProductAvailabilityData, ReportingRate
from logistics_project.apps.malawi.warehouse import warehouse_view
from logistics_project.apps.malawi.util import get_country_sp, fmt_pct,\
    hsa_supply_points_below
from logistics_project.apps.malawi.warehouse.report_utils import get_hsa_url

class View(warehouse_view.MalawiWarehouseView):

    def custom_context(self, request):

        if request.GET.get('hsa_code'):
            hsa = SupplyPoint.objects.filter(code=request.GET.get('hsa_code'))
            if hsa.count():
                self.slug = 'single_hsa'
                return self.single_hsa_context(request, hsa[0])
            else:
                messages.warning(request, "HSA does not exist or is not active")
        
        table = {
            "id": "all-hsas",
            "is_datatable": True,
            "header": ["Facility", "Name", "Id", "Responsible for these Commodities",\
                "Has Stockouts","Has Emergency Levels","Has Products with good supply",\
                "Has Overstocks", "Last Message Date"],
            "data": [],
        }

        sp = SupplyPoint.objects.get(location=request.location)\
            if request.location else get_country_sp()

        hsas = hsa_supply_points_below(sp.location)

        for hsa in hsas:
            up = UserProfileData.objects.get(supply_point=hsa)
            pads = ProductAvailabilityDataSummary.objects.filter(supply_point=hsa).order_by('-date')[0]
            table["data"].append({"url": get_hsa_url(hsa), "data": [hsa.supplied_by.name, hsa.name,\
                hsa.code, up.products_managed,\
                _yes_or_no(pads.any_without_stock), _yes_or_no(pads.any_emergency_stock),\
                _yes_or_no(pads.any_good_stock), _yes_or_no(pads.any_over_stock),\
                _date_fmt(up.last_message.date)]})

        table["height"] = min(480, hsas.count()*60)

        return {
                "table": table,
        }

    def single_hsa_context(self, request, hsa):

        report_table = {
            "id": "hsa-reporting-summary",
            "is_datatable": False,
            "header": ["Month", "On Time", "Late", "Complete"],
            "data": [],
        }

        reports = ReportingRate.objects.filter(supply_point=hsa).order_by('-date')[:3]
        for rr in reports.reverse():
            report_table["data"].append([rr.date.strftime('%b-%Y'), _yes_or_no(rr.on_time),\
                _yes_or_no(rr.late), _yes_or_no(rr.complete)])

        table2 = {
            "id": "calc-consumption-stock-levels",
            "is_datatable": False,
            "header": ["Product", "Total Calc Cons", "Avg Rep Rate", "AMC", "Total SOH", "Avg MOS",
                "Avg Days Stocked Out", "Total Adj Calc Cons", "Resupply Qts Required"],
            "data": [['CC', 33, 42, 53, 23, 0, 2, 4, 2]],
        }

        request_table = {
            "id": "order-response-time",
            "is_datatable": True,
            "header": ["Product", "Is Emergency", "Balance", "Amt Requested", "Amt Received", "Requested On",
                "Responded On", "Received On", "Status"],
            "data": [],
        }

        stock_requests = StockRequest.objects.filter(supply_point=hsa).order_by('-requested_on')
        for sr in stock_requests:
            request_table["data"].append([sr.product.name, _yes_or_no(sr.is_emergency), sr.balance, sr.amount_requested,\
                sr.amount_received, _date_fmt(sr.requested_on), _date_fmt(sr.responded_on),\
                _date_fmt(sr.received_on), sr.status])

        request_table["height"] = min(240, stock_requests.count()*60)

        msgs_table = {
            "id": "recent-messages",
            "is_datatable": False,
            "header": ["Date", "Message Text"],
            "data": [],
        }

        if hsa.contacts().count() > 0:
            contact = hsa.contacts()[0]

            msgs = Message.objects.filter(direction='I', contact=contact).order_by('-date')[:10]
            for msg in msgs:
                msgs_table["data"].append([_date_fmt(msg.date), msg.text])

        details_table = {
            "id": "hsa-details",
            "is_datatable": False,
            "header": ["", ""],
            "data": [],
        }

        up = UserProfileData.objects.get(supply_point=hsa)
        details_table["data"].append(['Facility', hsa.supplied_by.name])
        details_table["data"].append(['Phone Number', up.contact_info])
        details_table["data"].append(['Code', hsa.code])
        details_table["data"].append(['Products', up.products_managed])

        return {
                "report_table": report_table,
                "table2": table2,
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
    return "None"

