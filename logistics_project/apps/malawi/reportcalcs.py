from __future__ import absolute_import
from datetime import timedelta, datetime
from django.conf import settings
from django.template.loader import render_to_string
from django.template import TemplateDoesNotExist
from logistics.models import ProductStock, StockRequest, Product, SupplyPoint
from logistics.reports import ReportingBreakdown, calc_percentage
from logistics_project.apps.malawi.util import get_em_districts, hsa_supply_points_below,\
    get_ept_districts, facility_supply_points_below
from collections import defaultdict, OrderedDict
from logistics.charts import amc_plot
from static.malawi.config import SupplyPointCodes, BaseLevel

PRODUCT_CODES = ['co', 'or', 'zi', 'la', 'lb', 'dm', 'pa'] # Amox?


def _common_report(instance, context):
    try:
        r = render_to_string(instance.definition.template, context)
        return r
    except TemplateDoesNotExist:
        return render_to_string("malawi/partials/monitoring_reports/not_found.html", context)

def _update_dict(totals, to_add):
    for k, v in to_add.items():
        if k in totals:
            totals[k] += v
        else:
            totals[k] = v

def _district_breakdown(datespan, facility=False):
    """
    Breakdown of reporting information, by group and district
    """
    em = get_em_districts()
    ept = get_ept_districts()
    em_reports = OrderedDict()
    ept_reports = OrderedDict()
    em_totals = defaultdict(lambda: 0)
    ept_totals = defaultdict(lambda: 0)
    em_totals.update({'no_stockouts_pct_p':{},
                      'no_stockouts_p':{},
                      'stockouts_duration_p':{},
                      'stockouts_avg_duration_p':{},
                      'totals_p':{},
                      'discrepancies_p': {},
                      'discrepancies_tot_p': {},
                      'discrepancies_pct_p': {},
                      'discrepancies_avg_p': {},
                      'filled_orders_p': {},
                      'req_times':[]})
    ept_totals.update({'no_stockouts_pct_p':{},
                       'no_stockouts_p':{},
                       'stockouts_duration_p':{},
                       'stockouts_avg_duration_p':{},
                       'totals_p':{},
                       'discrepancies_p': {},
                       'discrepancies_pct_p': {},
                       'discrepancies_tot_p': {},
                       'discrepancies_avg_p': {},
                       'filled_orders_p': {},
                       'req_times':[]})

    for d in em:    
        if facility:
            bd = ReportingBreakdown(facility_supply_points_below(d),
                                    datespan, MNE=True)
        else:
            bd = ReportingBreakdown(hsa_supply_points_below(d),
                                   datespan, MNE=True)
        em_reports[d] = _to_totals(bd)
        _update_dict(em_totals, em_reports[d])
        em_totals['req_times'] += bd.req_times
        em_reports[d]['no_stockouts_pct_p'] = bd.no_stockouts_pct_p
        em_reports[d]['no_stockouts_p'] = bd.no_stockouts_p
        em_reports[d]['totals_p'] = bd.totals_p
        em_reports[d]['avg_req_time'] = bd.avg_req_time
        em_reports[d]['discrepancies_pct_p'] = bd.discrepancies_pct_p
        em_reports[d]['discrepancies_avg_p'] = bd.discrepancies_avg_p
        em_reports[d]['discrepancies_tot_p'] = bd.discrepancies_tot_p
        em_reports[d]['discrepancies_p'] = bd.discrepancies_p
        em_reports[d]['stockouts_duration_p'] = bd.stockouts_duration_p

        em_reports[d]['stockouts_avg_duration_p'] = bd.stockouts_avg_duration_p
        _update_dict(em_totals['stockouts_duration_p'], bd.stockouts_duration_p)
        _update_dict(em_totals['no_stockouts_p'], bd.no_stockouts_p)
        _update_dict(em_totals['discrepancies_p'], bd.discrepancies_p)
        _update_dict(em_totals['discrepancies_tot_p'], bd.discrepancies_tot_p)
        _update_dict(em_totals['filled_orders_p'], bd.filled_orders_p)
        _update_dict(em_totals['totals_p'], bd.totals_p)

    for d in ept:
        if facility:
            bd = ReportingBreakdown(facility_supply_points_below(d),
                                    datespan, MNE=True)
        else:
            bd = ReportingBreakdown(hsa_supply_points_below(d),
                                   datespan, MNE=True)
        ept_reports[d] = _to_totals(bd)
        _update_dict(ept_totals, ept_reports[d])
        ept_totals['req_times'] += bd.req_times
        ept_reports[d]['no_stockouts_pct_p'] = bd.no_stockouts_pct_p
        ept_reports[d]['no_stockouts_p'] = bd.no_stockouts_p
        ept_reports[d]['totals_p'] = bd.totals_p
        ept_reports[d]['discrepancies_pct_p'] = bd.discrepancies_pct_p
        ept_reports[d]['discrepancies_avg_p'] = bd.discrepancies_avg_p
        ept_reports[d]['discrepancies_tot_p'] = bd.discrepancies_tot_p
        ept_reports[d]['discrepancies_p'] = bd.discrepancies_p
        ept_reports[d]['avg_req_time'] = bd.avg_req_time
        ept_reports[d]['stockouts_duration_p'] = bd.stockouts_duration_p
        ept_reports[d]['stockouts_avg_duration_p'] = bd.stockouts_avg_duration_p
        _update_dict(ept_totals['no_stockouts_p'], bd.no_stockouts_p)
        _update_dict(ept_totals['stockouts_duration_p'], bd.stockouts_duration_p)
        _update_dict(ept_totals['discrepancies_p'], bd.discrepancies_p)
        _update_dict(ept_totals['discrepancies_tot_p'], bd.discrepancies_tot_p)
        _update_dict(ept_totals['filled_orders_p'], bd.filled_orders_p)
        _update_dict(ept_totals['totals_p'], bd.totals_p)

    for p in ept_totals['stockouts_duration_p']:
        ept_totals['stockouts_avg_duration_p'][p] = timedelta(seconds=sum(ept_totals['stockouts_duration_p'][p])/len(ept_totals['stockouts_duration_p'][p]))
        
    for p in em_totals['stockouts_duration_p']:
        em_totals['stockouts_avg_duration_p'][p] = timedelta(seconds=sum(em_totals['stockouts_duration_p'][p])/len(em_totals['stockouts_duration_p'][p]))

    for p in ept_totals['no_stockouts_p']:
        ept_totals['no_stockouts_pct_p'][p] = calc_percentage(ept_totals['no_stockouts_p'][p], ept_totals['totals_p'][p])
        
    for p in em_totals['no_stockouts_p']:
        em_totals['no_stockouts_pct_p'][p] = calc_percentage(em_totals['no_stockouts_p'][p], em_totals['totals_p'][p])

    for p in ept_totals['discrepancies_p']:
        ept_totals['discrepancies_pct_p'][p] = calc_percentage(ept_totals['discrepancies_p'][p], ept_totals['filled_orders_p'][p])
        if ept_totals['discrepancies_p'][p]: ept_totals['discrepancies_avg_p'][p] = float(ept_totals['discrepancies_tot_p'][p]) / ept_totals['discrepancies_p'][p]

    for p in em_totals['discrepancies_p']:
        em_totals['discrepancies_pct_p'][p] = calc_percentage(em_totals['discrepancies_p'][p], em_totals['filled_orders_p'][p])
        if em_totals['discrepancies_p'][p]: em_totals['discrepancies_avg_p'][p] = float(em_totals['discrepancies_tot_p'][p]) / em_totals['discrepancies_p'][p]

    if len(em_totals['req_times']):
        em_totals['req_times'] = timedelta(seconds=sum(em_totals['req_times'])/len(em_totals['req_times']))
    else:
        em_totals['req_times'] = None
    if len(ept_totals['req_times']):
        ept_totals['req_times'] = timedelta(seconds=sum(ept_totals['req_times'])/len(ept_totals['req_times']))
    else:
        ept_totals['req_times'] = None

    return {"em_reports": em_reports,
            "ept_reports": ept_reports,
            "em_totals": em_totals,
            "ept_totals": ept_totals}
    
def _to_totals(bd):
    """
    Convert a ReportingBreakdown object into totals for tabular viewing
    """
    return {"late": len(bd.reported_late), 
            "on_time": len(bd.on_time),
            "non_reporting": len(bd.non_reporting),
            "fully_reporting": len(bd.full),
            "partially_reporting": len(bd.partial),
            "unconfigured": len(bd.unconfigured),
            "stockouts": len(bd.stockouts),
            "emergency": len(bd.emergency),
            "stockouts_emergency": len(bd.stockouts_emergency),
            "total": len(bd.supply_points)}


def em_late_reporting(instance):
    """
    HSAs who reported late (after 2nd of the month), by District 
    """
    districts = get_em_districts()
    reports = OrderedDict()
    totals = defaultdict(lambda: 0)
    for d in districts:
        bd = ReportingBreakdown(hsa_supply_points_below(d), 
                                instance.datespan, 
                                include_late=True,
                                days_for_late=settings.LOGISTICS_DAYS_UNTIL_LATE_PRODUCT_REPORT,
                                MNE=True)
        reports[d] = _to_totals(bd)
        _update_dict(totals, reports[d])
    
    return _common_report(instance, {"reports": reports, "totals": totals}) 
    
def hsas_reporting(instance):
    """
    HSAs who reported at least once, by District and group
    """
    return _common_report(instance, _district_breakdown(instance.datespan)) 

def reporting_completeness(instance):
    """
    HSA orders that are complete, by District  and group
    """
    return _common_report(instance, _district_breakdown(instance.datespan)) 

def fully_stocked_hsas(instance):
    """
    No stock outs reported in past 30 days by HSAs by product, by District and group
    """
    d = _district_breakdown(instance.datespan)
    d['product_codes'] = PRODUCT_CODES

    return _common_report(instance, d)


def fully_stocked_facilities(instance):
    """
    No stock outs reported by HCs in past 30 days by product, by District and group
    """
    d = _district_breakdown(instance.datespan, facility=True)
    d['product_codes'] = PRODUCT_CODES

    return _common_report(instance, d)

def hsa_stockout_duration(instance):
    """
    Duration of HSA stockout by product over past, by District and group
    """
    d = _district_breakdown(instance.datespan)
    d['product_codes'] = PRODUCT_CODES
    return _common_report(instance, d)

def facility_stockout_duration(instance):
    """
    Duration of HC stockout by product over past, by District and group
    """
    d = _district_breakdown(instance.datespan, facility=True)
    d['product_codes'] = PRODUCT_CODES
    return _common_report(instance, d)

def emergency_orders(instance):
    """
    Emergency orders reported by HSAs, by District and group
    """
    return _common_report(instance, _district_breakdown(instance.datespan))

def order_discrepancies(instance):
    """
    HSA orders with more than 20% under/over discrepancy between order and receipt by product, by District and group (last 30 days)
    """
    d = _district_breakdown(instance.datespan)
    d['product_codes'] = PRODUCT_CODES
    return _common_report(instance, d)

def order_messages(instance):
    """
    List of order messages sent by cStock to HC, by HC, by time period
    """

    # Unfortunately there's no good way to determine what StockRequests were part of the same order.  We fudge it
    # by checking to see if their submission times are identical down to the nanosecond.
    sr = StockRequest.objects.select_related().filter(requested_on__gt=instance.datespan.startdate,
                                                      requested_on__lt=instance.datespan.enddate,
                                                      supply_point__active=True,
                                                      supply_point__type__code=SupplyPointCodes.HSA)
    if instance.location:
        sr = sr.filter(supply_point__in=hsa_supply_points_below(instance.location))
    rows = []
    for r in sr.values_list('requested_on', flat=True).distinct().order_by('requested_on'):
        srf = sr.filter(requested_on=r)
        if not srf.exists(): continue # This should never happen, but just checking...
        if len(srf.values_list('supply_point', flat=True).distinct()) != 1:
            # This should never happen but we check for it nonetheless and apply a stupid fix.
            # TODO: Maybe do something reasonable here?
            srf = srf.filter(supply_point=srf[0].supply_point)
        row = {'hsa': srf[0].supply_point.name,
               'hsa_id': srf[0].supply_point.code,
               'requested_on': r,
               'received_on': None,
               'products': {},
               'product_statuses': {},
               'status': ""}
        count = 0
        statuses = set()
        for p in PRODUCT_CODES:
            if srf.filter(product__sms_code=p).exists():
                count += 1
                g = srf.filter(product__sms_code=p)[0]
                s = g.status if g.status != 'canceled' else 'superseded'
                if not s in row['status']:
                    if row['status']:
                        row['status'] += ", <span class='order-%s'>%s</span>" % (s,s.replace('_', ' '))
                    else: row['status'] = "<span class='order-%s'>%s</span>" % (s,s.replace('_', ' '))
                if g.status == 'received': row['received_on'] = g.received_on # We assume all portions of an order are picked up at the same time.
                row['products'][p] = g.amount_requested
                row['product_statuses'][p] = g.status
            else:
                row['products'][p] = "<span class='n-a'>n/a</span>"
        if not row['status']:
            row['status'] = "<span class='n-a'>n/a</span>"
        if count:
            rows.append(row)
    return _common_report(instance, {'product_codes': PRODUCT_CODES,
                                     'rows': rows})

def order_times(instance):
    """
    Time between HSA order and receipt, by District and group (hours)
    """
    return _common_report(instance, _district_breakdown(instance.datespan))

def hsas_with_stock(instance):
    """
    HSA with adequate stock, by District and group
    """
    ps = ProductStock.objects.select_related().filter(quantity__gt=0, product__sms_code__in=PRODUCT_CODES)
    em = get_em_districts()
    ept = get_ept_districts()
    em_reports = {}
    ept_reports = {}
    em_totals = {}
    ept_totals = {}
    em_users = {}
    ept_users = {}
    em_total_u = {}
    ept_total_u = {}

    # There is just no good way to do this.  The performance here is going to suck and there's no way around it.
    for p in PRODUCT_CODES:
        em_totals[p] = 0
        ept_totals[p] = 0
        em_total_u[p] = 0
        ept_total_u[p] = 0

    for d in em:
        em_reports[d] = {}
        em_users[d] = {}
        for p in PRODUCT_CODES:
            em_reports[d][p] = len([px for px in ps.filter(product__sms_code=p, supply_point__in=hsa_supply_points_below(d)) if px.is_in_adequate_supply()])
            em_users[d][p] = len([px for px in ps.filter(product__sms_code=p, supply_point__in=hsa_supply_points_below(d))])
            em_totals[p] += em_reports[d][p]
            em_total_u[p] += em_users[d][p]
    for d in ept:
        ept_reports[d] = {}
        ept_users[d] = {}
        for p in PRODUCT_CODES:
            ept_reports[d][p] = len([px for px in ps.filter(product__sms_code=p, supply_point__in=hsa_supply_points_below(d)) if px.is_in_adequate_supply()])
            ept_users[d][p] = len([px for px in ps.filter(product__sms_code=p, supply_point__in=hsa_supply_points_below(d))])
            ept_totals[p] += ept_reports[d][p]
            ept_total_u[p] += ept_users[d][p]

    instance.datespan = None
    return _common_report(instance, {'product_codes': PRODUCT_CODES,
                                     'em_reports':em_reports,
                                     'em_users':em_users,
                                     'ept_reports':ept_reports,
                                     'ept_users':ept_users,
                                     'em_totals':em_totals,
                                     'ept_totals':ept_totals,
                                     'em_total_u':em_total_u,
                                     'ept_total_u':ept_total_u})

def amc_over_time(instance):
    """
    Average monthly consumption, plotted over time
    """
    products = Product.objects.filter(type__base_level=BaseLevel.HSA).order_by('sms_code')
    supply_points = SupplyPoint.objects.filter(active=True, type__code=SupplyPointCodes.HSA)
    data, data_rows = amc_plot(supply_points, instance.datespan, products=products)
    return _common_report(instance, {'chart_data': data,
                                     'data_rows': data_rows,
                                     'products': products,
                                     'datetimes': [datetime(m, y, 1) for m, y in instance.datespan.months_iterator()],
                                     'datespan': instance.datespan})

def average_discrepancies(instance):
    """
    Average discrepancy between order and receipt per product, by District
    """
    product_codes = PRODUCT_CODES 
    d = _district_breakdown(instance.datespan)
    d['product_codes'] = product_codes
    return _common_report(instance, d)
