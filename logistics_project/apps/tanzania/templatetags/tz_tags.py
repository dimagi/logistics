from django import template
from logistics.util import config
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from logistics.models import Product, ProductReport
from django.template.loader import render_to_string
from logistics.const import Reports
from logistics_project.apps.tanzania.utils import latest_lead_time
from datetime import timedelta

register = template.Library()

@register.simple_tag
def product_inventory(facility, view_type):
    return render_to_string("tanzania/partials/product_inventory.html", 
                              {"view_type": view_type,
                               "product_stocks": facility.product_stocks().all()})

@register.simple_tag
def last_sms(facility):
    # really this should be called last stock on hand report
    # since that's all it looks for.
    reports = ProductReport.objects.filter(supply_point=facility, 
                                           report_type__code=Reports.SOH)\
                                           .order_by('-report_date')
    last_report = reports[0] if reports else None
    return render_to_string("tanzania/partials/last_sms.html", 
                              {"facility": facility,
                               "last_report": last_report})
@register.simple_tag
def get_map_popup(supply_point, request):
    return render_to_string("tanzania/partials/map_popup.html", 
                            {"sp": supply_point, 
                             "productstocks": supply_point.productstock_set.all().order_by('product__name')}
                            ).replace("\n", "")

@register.simple_tag
def contact_list(supply_point, recurse=True, recurse_depth=100, current_depth=0, 
                 currently_rendered=""):
    this_rendering = render_to_string("tanzania/partials/contact_table.html",
                                      {"supply_point": supply_point,
                                       "contacts": supply_point.contact_set.all()})
    this_depth = "%s%s" % (currently_rendered, this_rendering)
    if recurse and supply_point.supplied_by and current_depth < recurse_depth:
        return contact_list(supply_point.supplied_by, recurse, 
                            recurse_depth, current_depth + 1, this_depth)
    else:
        return this_depth
    
    
@register.simple_tag
def lead_time(supply_point):
    ltime = latest_lead_time(supply_point)
    return render_to_string("tanzania/partials/lead_time.html", 
                            {"lead_time": ltime})
    
@register.simple_tag
def average_lead_time(supply_point_list):
    total_time = timedelta(days=0)
    count = 0
    for supply_point in supply_point_list:
        ltime = latest_lead_time(supply_point)
        if ltime is not None:
            total_time += ltime
            count += 1
    
    average_time = total_time / count if count else None
    return render_to_string("tanzania/partials/lead_time.html", 
                            {"lead_time": average_time})
    

            