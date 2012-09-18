from django import template
from logistics.models import SupplyPoint
from logistics.templatetags.logistics_report_tags import r_2_s_helper
from logistics_project.apps.malawi.warehouse.report_utils import WarehouseProductAvailabilitySummary
from logistics_project.apps.malawi.util import get_country_sp

register = template.Library()

@register.simple_tag
def warehouse_product_availability_summary(location, date, width=900, height=300):
    sp = SupplyPoint.objects.get(location=location) if location else get_country_sp()
    summary = WarehouseProductAvailabilitySummary(sp, date, width, height)
    return r_2_s_helper("logistics/partials/product_availability_summary.html", 
                         {"summary": summary})
