from django.template.loader import render_to_string
from django.template import TemplateDoesNotExist
from logistics.apps.logistics.reports import ReportingBreakdown
from logistics.apps.malawi.util import get_em_districts, hsa_supply_points_below
from django.utils.datastructures import SortedDict
from collections import defaultdict

def _common_report(instance, context):
    try: 
        return render_to_string(instance.definition.template, context)
    except TemplateDoesNotExist:
        return render_to_string("malawi/partials/monitoring_reports/not_found.html", context)

def em_late_reporting(instance):
    districts = get_em_districts()
    reports = SortedDict()
    totals = defaultdict(lambda: 0)
    def _update_totals(d):
        for k, v in d.items():
            totals[k] += v
    for d in districts:
        bd = ReportingBreakdown(hsa_supply_points_below(d), 
                                instance.datespan, 
                                include_late=True,
                                days_for_late=2)
        reports[d] = {"late": len(bd.reported_late), 
                      "on_time": len(bd.on_time),
                      "non_reporting": len(bd.non_reporting),
                      "total": len(bd.supply_points)}
        _update_totals(reports[d])
    
    return _common_report(instance, {"reports": reports, "totals": totals}) 
    
def hsas_reporting(instance):
    return _common_report(instance, {}) 

def reporting_completeness(instance):
    return _common_report(instance, {}) 

def fully_stocked_hsas(instance):
    return _common_report(instance, {}) 

def fully_stocked_facilities(instance):
    return _common_report(instance, {}) 

def hsa_stockout_duration(instance):
    return _common_report(instance, {}) 

def facility_stockout_duration(instance):
    return _common_report(instance, {}) 

def emergency_orders(instance):
    return _common_report(instance, {}) 

def order_discrepancies(instance):
    return _common_report(instance, {}) 

def order_messages(instance):
    return _common_report(instance, {}) 

def order_times(instance):
    return _common_report(instance, {}) 

def hsas_with_stock(instance):
    return _common_report(instance, {}) 

def average_discrepancies(instance):
    return _common_report(instance, {}) 
