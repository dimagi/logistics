from django.template.loader import render_to_string
from django.template import TemplateDoesNotExist
from logistics.apps.logistics.reports import ReportingBreakdown, calc_percentage
from logistics.apps.malawi.util import get_em_districts, hsa_supply_points_below,\
    get_ept_districts
from django.utils.datastructures import SortedDict
from collections import defaultdict

def _common_report(instance, context):
    try: 
        return render_to_string(instance.definition.template, context)
    except TemplateDoesNotExist:
        return render_to_string("malawi/partials/monitoring_reports/not_found.html", context)

def _update_dict(totals, to_add):
    for k, v in to_add.items():
        if k in totals:
            totals[k] += v
        else:
            totals[k] = v

def _district_breakdown(datespan):
    """
    Breakdown of reporting information, by group and district
    """
    em = get_em_districts()
    ept = get_ept_districts()
    em_reports = SortedDict()
    ept_reports = SortedDict()
    em_totals = defaultdict(lambda: 0)
    ept_totals = defaultdict(lambda: 0)
    em_totals.update({'no_stockouts_pct_p':{}, 'no_stockouts_p':{}, 'totals_p':{}})
    ept_totals.update({'no_stockouts_pct_p':{}, 'no_stockouts_p':{}, 'totals_p':{}})

    for d in em:
        bd = ReportingBreakdown(hsa_supply_points_below(d), 
                                datespan)
        em_reports[d] = _to_totals(bd)
        _update_dict(em_totals, em_reports[d])
#        em_reports[d]['stockouts_p'] = bd.stockouts_p
        em_reports[d]['no_stockouts_pct_p'] = bd.no_stockouts_pct_p
        _update_dict(em_totals['no_stockouts_p'], bd.no_stockouts_p)
        _update_dict(em_totals['totals_p'], bd.totals_p)

    for d in ept:
        bd = ReportingBreakdown(hsa_supply_points_below(d), 
                                datespan)
        ept_reports[d] = _to_totals(bd)
        _update_dict(ept_totals, ept_reports[d])
        ept_reports[d]['no_stockouts_pct_p'] = bd.no_stockouts_pct_p
        ept_reports[d]['totals_p'] = bd.totals_p
        _update_dict(ept_totals['no_stockouts_p'], bd.no_stockouts_p)
        _update_dict(ept_totals['totals_p'], bd.totals_p)


    for p in ept_totals['no_stockouts_p']:
        ept_totals['no_stockouts_pct_p'][p] = calc_percentage(ept_totals['no_stockouts_p'][p], ept_totals['totals_p'][p])
        
    for p in em_totals['no_stockouts_p']:
        em_totals['no_stockouts_pct_p'][p] = calc_percentage(em_totals['no_stockouts_p'][p], em_totals['totals_p'][p])


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
            "stockouts_emergency": len(bd.stockouts_emergency),
            "total": len(bd.supply_points)}

def em_late_reporting(instance):
    """
    HSAs who reported late (after 2nd of the month), by District 
    """
    districts = get_em_districts()
    reports = SortedDict()
    totals = defaultdict(lambda: 0)
    for d in districts:
        bd = ReportingBreakdown(hsa_supply_points_below(d), 
                                instance.datespan, 
                                include_late=True,
                                days_for_late=2)
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
    product_codes = ['co', 'or', 'zi', 'la', 'lb'] #Depo? Amox?
    d = _district_breakdown(instance.datespan)
    d['product_codes'] = product_codes

    return _common_report(instance, d)


def fully_stocked_facilities(instance):
    """
    No stock outs reported by HCs in past 30 days by product, by District and group
    """
    return _common_report(instance, {}) 

def hsa_stockout_duration(instance):
    """
    Duration of HSA stockout by product over past, by District and group
    """
    return _common_report(instance, {}) 

def facility_stockout_duration(instance):
    """
    Duration of HC stockout by product over past, by District and group
    """
    return _common_report(instance, {}) 

def emergency_orders(instance):
    """
    Emergency orders reported by HSAs, by District and group
    """
    return _common_report(instance, _district_breakdown(instance.datespan))

def order_discrepancies(instance):
    """
    HSA orders with discrepancy between order and receipt by product, by District and group
    """
    return _common_report(instance, {}) 

def order_messages(instance):
    """
    List of order messages sent by cStock to HC, by HC, by time period
    """
    return _common_report(instance, {}) 

def order_times(instance):
    """
    Time between HSA order and receipt, by District and group (hours)
    """
    return _common_report(instance, {}) 

def hsas_with_stock(instance):
    """
    HSA with adequate stock, by District and group
    """
    return _common_report(instance, {}) 

def average_discrepancies(instance):
    """
    Average discrepancy  between order and receipt per product, by District
    """
    return _common_report(instance, {}) 
