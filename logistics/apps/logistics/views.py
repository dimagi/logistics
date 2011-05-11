#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
import gviz_api

import settings
from random import randint
from datetime import datetime
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import permission_required
from django.db.models import Q
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django_tablib import ModelDataset
from django_tablib.base import mimetype_map
from rapidsms.contrib.locations.models import Location
from logistics.apps.logistics.models import ProductStock, \
    ProductReportsHelper, Product, ProductType, ProductReport, \
    get_geography, STOCK_ON_HAND_REPORT_TYPE, DISTRICT_TYPE, LogisticsProfile,\
    SupplyPoint
from logistics.apps.logistics.view_decorators import filter_context, geography_context
from .models import Product
from .forms import FacilityForm, CommodityForm
from .tables import FacilityTable, CommodityTable
import json

def no_ie_allowed(request, template="logistics/no_ie_allowed.html"):
    return render_to_response(template, context_instance=RequestContext(request))

def landing_page(request):
    if 'MSIE' in request.META['HTTP_USER_AGENT']:
        return no_ie_allowed(request)
    prof = None 
    try:
        if not request.user.is_anonymous():
            prof = request.user.get_profile()
    except LogisticsProfile.DoesNotExist:
        pass
    
    if prof and prof.facility:
        return stockonhand_facility(request, request.user.get_profile().facility.code)
    elif prof and prof.location:
        return aggregate(request, request.user.get_profile().location.code)
    return dashboard(request)

def input_stock(request, facility_code, context={}, template="logistics/input_stock.html"):
    # TODO: replace this with something that depends on the current user
    # QUESTION: is it possible to make a dynamic form?
    errors = ''
    rms = get_object_or_404(SupplyPoint, code=facility_code)
    productstocks = [p for p in ProductStock.objects.filter(supply_point=rms).order_by('product')]
    if request.method == "POST":
        # we need to use the helper/aggregator so that when we update
        # the supervisor on resolved stockouts we can do it all in a
        # single message
        prh = ProductReportsHelper(rms, STOCK_ON_HAND_REPORT_TYPE)
        for stock in productstocks:
            try:
                if stock.product.sms_code in request.POST:
                    quantity = request.POST[stock.product.sms_code].strip()
                    if quantity:
                        if not quantity.isdigit():
                            errors = ", ".join([errors, stock.product.name])
                            continue
                        prh.add_product_stock(stock.product.sms_code, quantity, save=False)
                if "%s_receipt" % stock.product.sms_code in request.POST:
                    receipt = request.POST["%s_receipt" % stock.product.sms_code].strip()
                    if not receipt.isdigit():
                        errors = ", ".join([errors, stock.product.name])
                        continue
                    if int(receipt) != 0:
                        prh.add_product_receipt(stock.product.sms_code, receipt, save=False)
                if "%s_consumption" % stock.product.sms_code in request.POST:
                    consumption = request.POST["%s_consumption" % stock.product.sms_code].strip()
                    if consumption:
                        if not consumption.isdigit():
                            errors = ", ".join([errors, stock.product.name])
                            continue
                        prh.add_product_consumption(stock.product, consumption)
                if "%s_is_active" % stock.product.sms_code in request.POST:
                    rms.activate_product(stock.product)
                else:
                    rms.deactivate_product(stock.product)
            except ValueError, e:
                errors = errors + unicode(e)
        if not errors:
            prh.save()
            return HttpResponseRedirect(reverse(stockonhand_facility, args=(rms.code,)))
        errors = "Please enter all stock on hand and consumption as integers, for example:'100'. " + \
                 "The following fields had problems: " + errors.strip(', ')
    return render_to_response(
        template, {
                'errors': errors,
                'rms': rms,
                'productstocks': productstocks,
                'date': datetime.now()
            }, context_instance=RequestContext(request)
    )

class JSONDateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return "Date(%d, %d, %d)" % (obj.year, obj.month, obj.day)
        else:
            return json.JSONEncoder.default(self, obj)

@geography_context
def stockonhand_facility(request, facility_code, context={}, template="logistics/stockonhand_facility.html"):
    """
     this view currently only shows the current stock on hand for a given facility
    """
    facility = get_object_or_404(SupplyPoint, code=facility_code)
    stockonhands = ProductStock.objects.filter(supply_point=facility).order_by('product')
    last_reports = ProductReport.objects.filter(supply_point=facility).order_by('-report_date')

    if last_reports:
        context['last_reported'] = last_reports[0].report_date
        cols = {"date": ("datetime", "Date")}
        for s in stockonhands:
            cols[s.product.name] = ('number', s.product.sms_code)#, {'type': 'string', 'label': "title_"+s.sms_code}]
        table = gviz_api.DataTable(cols)

        data_rows = {}
        for r in last_reports:
            if not r.report_date in data_rows: data_rows[r.report_date] = {}
            data_rows[r.report_date][r.product.name] = r.quantity
        rows = []
        for d in data_rows.keys():
            q = {"date":d}
            q.update(data_rows[d])
            rows += [q]
        table.LoadData(rows)
        raw_data = table.ToJSCode("raw_data", columns_order=["date"] + [x for x in cols.keys() if x != "date"],
                                  order_by="date")
        if len(raw_data)>0:
            context['raw_data'] = raw_data

    context['stockonhands'] = stockonhands
    context['facility'] = facility
    context["location"] = facility.location
    return render_to_response(
        template, context, context_instance=RequestContext(request)
    )

@geography_context
@filter_context
def district(request, location_code, context={}, template="logistics/aggregate.html"):
    """
    The district view is unusual. When we do not receive a filter by individual product,
    we show the aggregate report. When we do receive a filter by individual product, we show
    the 'by product' report. Let's see how this goes. 
    """
    location = get_object_or_404(Location, code=location_code)
    context['location'] = location
    context['stockonhands'] = stockonhands = ProductStock.objects.filter(supply_point__location=location)
    commodity_filter = None
    commoditytype_filter = None
    if request.method == "POST" or request.method == "GET":
        # We support GETs so that folks can share this report as a url
        if 'commodity' in request.REQUEST and request.REQUEST['commodity'] != 'all':
            commodity_filter = request.REQUEST['commodity']
            context['commodity_filter'] = commodity_filter
            commodity = Product.objects.get(sms_code=commodity_filter)
            context['commoditytype_filter'] = commodity.type.code
            template="logistics/stockonhand_district.html"
            context['stockonhands'] = stockonhands.filter(product=commodity).order_by('supply_point__name')
        elif 'commoditytype' in request.REQUEST and request.REQUEST['commoditytype'] != 'all':
            commoditytype_filter = request.REQUEST['commoditytype']
            context['commoditytype_filter'] = commoditytype_filter
            type = ProductType.objects.get(code=commoditytype_filter)
            context['commodities'] = context['commodities'].filter(type=type)
            context['stockonhands'] = stockonhands.filter(product__type=type).order_by('supply_point__name')
    context['rows'] =_get_location_children(location, commodity_filter, commoditytype_filter)
    return render_to_response(
        template, context, context_instance=RequestContext(request)
    )

@geography_context
def reporting(request, location_code=None, context={}, template="logistics/reporting.html"):
    """ which facilities have reported on time and which haven't """
    seven_days_ago = datetime.now() + relativedelta(days=-7)
    context['late_facilities'] = SupplyPoint.objects.filter(Q(last_reported__lt=seven_days_ago) | Q(last_reported=None)).order_by('-last_reported','name')
    context['on_time_facilities'] = SupplyPoint.objects.filter(last_reported__gte=seven_days_ago).order_by('-last_reported','name')
    return render_to_response(
        template, context, context_instance=RequestContext(request)
    )

@geography_context
@filter_context
def dashboard(request, location_code=None, context={}, template="logistics/aggregate.html"):
    if location_code is None:
        location_code = settings.COUNTRY
    location = get_object_or_404(Location, code=location_code)
    # if the location has no children, and 1 supply point treat it like
    # a stock on hand request. Otherwise treat it like an aggregate.
    if location.children().count() == 0 and location.facilities().count() == 1:
        return stockonhand_facility(request, location_code)
    return aggregate(request, location_code )

@geography_context
@filter_context
def aggregate(request, location_code=None, context={}, template="logistics/aggregate.html"):
    """
    The aggregate view of all children within a geographical region
    where 'children' can either be sub-regions
    OR facilities if no sub-region exists
    """
    commodity_filter = None
    commoditytype_filter = None
    if request.method == "POST" or request.method == "GET":
        # We support GETs so that folks can share this report as a url
        if 'commodity' in request.REQUEST and request.REQUEST['commodity'] != 'all':
            commodity_filter = request.REQUEST['commodity']
            context['commodity_filter'] = commodity_filter
            commodity = Product.objects.get(sms_code=commodity_filter)
            context['commoditytype_filter'] = commodity.type.code
        elif 'commoditytype' in request.REQUEST and request.REQUEST['commoditytype'] != 'all':
            commoditytype_filter = request.REQUEST['commoditytype']
            context['commoditytype_filter'] = commoditytype_filter
            type = ProductType.objects.get(code=commoditytype_filter)
            context['commodities'] = context['commodities'].filter(type=type)
    if location_code is None:
        location_code = settings.COUNTRY
    location = get_object_or_404(Location, code=location_code)
    context['location'] = location
    context['rows'] =_get_location_children(location, commodity_filter, commoditytype_filter)
    return render_to_response(
        template, context, context_instance=RequestContext(request)
    )

def _get_location_children(location, commodity_filter, commoditytype_filter):
    rows = []
    children = []
    children.extend(location.facilities())
    children.extend(location.children())
    for child in children:
        row = {}
        row['location'] = child
        row['is_active'] = child.is_active
        row['name'] = child.name
        row['code'] = child.code
        if isinstance(child, SupplyPoint):
            row['url'] = reverse('stockonhand_facility', args=[child.code])
        else:
            row['url'] = reverse('logistics_dashboard', args=[child.code])
        row['stockout_count'] = child.stockout_count(product=commodity_filter, 
                                                     producttype=commoditytype_filter)
        row['emergency_stock_count'] = child.emergency_stock_count(product=commodity_filter, 
                                                     producttype=commoditytype_filter)
        row['low_stock_count'] = child.low_stock_count(product=commodity_filter, 
                                                     producttype=commoditytype_filter)
        row['good_supply_count'] = child.good_supply_count(product=commodity_filter, 
                                                     producttype=commoditytype_filter)
        row['overstocked_count'] = child.overstocked_count(product=commodity_filter, 
                                                     producttype=commoditytype_filter)
        if commodity_filter is not None:
            row['consumption'] = child.consumption(product=commodity_filter, 
                                                   producttype=commoditytype_filter)
        rows.append(row)
    return rows

def export_stockonhand(request, facility_code, format='xls', filename='stockonhand'):
    class ProductReportDataset(ModelDataset):
        class Meta:
            queryset = ProductReport.objects.filter(supply_point__code=facility_code).order_by('report_date')
    dataset = getattr(ProductReportDataset(), format)
    filename = '%s_%s.%s' % (filename, facility_code, format)
    response = HttpResponse(
        dataset,
        mimetype=mimetype_map.get(format, 'application/octet-stream')
        )
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    return response

@permission_required('logistics.add_facility')
@transaction.commit_on_success
def facility(req, pk=None, template="logistics/config.html"):
    facility = None
    form = None
    klass = "SupplyPoint"
    if pk is not None:
        facility = get_object_or_404(
            SupplyPoint, pk=pk)
    if req.method == "POST":
        if req.POST["submit"] == "Delete %s" % klass:
            facility.delete()
            return HttpResponseRedirect(
                reverse('facility_view'))
        else:
            form = FacilityForm(instance=facility,
                                data=req.POST)
            if form.is_valid():
                facility = form.save()
                return HttpResponseRedirect(
                    reverse('facility_view'))
    else:
        form = FacilityForm(instance=facility)
    return render_to_response(
        template, {
            "table": FacilityTable(SupplyPoint.objects.all(), request=req),
            "form": form,
            "object": facility,
            "klass": klass,
            "klass_view": reverse('facility_view')
        }, context_instance=RequestContext(req)
    )

@permission_required('logistics.add_commodity')
@transaction.commit_on_success
def commodity(req, pk=None, template="logistics/config.html"):
    form = None
    commodity = None
    klass = "Commodity"
    if pk is not None:
        commodity = get_object_or_404(Product, pk=pk)
    if req.method == "POST":
        if req.POST["submit"] == "Delete %s" % klass:
            commodity.delete()
            return HttpResponseRedirect(
                reverse('commodity_view'))
        else:
            form = CommodityForm(
                                 instance=commodity,
                                 data=req.POST)
            if form.is_valid():
                commodity = form.save()
                return HttpResponseRedirect(
                    reverse('commodity_view'))
    else:
        form = CommodityForm(instance=commodity)
    return render_to_response(
        template, {
            "table": CommodityTable(Product.objects.all(), request=req),
            "form": form,
            "object": commodity,
            "klass": klass,
            "klass_view": reverse('commodity_view')
        }, context_instance=RequestContext(req)
    )
