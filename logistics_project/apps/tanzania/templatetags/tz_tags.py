from django import template
from logistics.util import config
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from logistics.models import Product, ProductReport
from django.template.loader import render_to_string
from logistics.const import Reports

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
