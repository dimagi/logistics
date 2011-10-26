from django import template
from logistics.models import ProductReport
from django.core.urlresolvers import reverse
from django.template.defaultfilters import floatformat
from django.template.loader import render_to_string
from logistics.const import Reports
from django.utils.functional import curry
from logistics_project.apps.tanzania.models import SupplyPointNote, OnTimeStates, SupplyPointStatusTypes
from logistics_project.apps.tanzania.utils import calc_lead_time, last_stock_on_hand, last_stock_on_hand_before, soh_reported_on_time, soh_on_time_reporting, historical_response_rate
from datetime import datetime, timedelta, time
from django.template import defaultfilters
from django.utils.translation import ugettext as _
from dimagi.utils.dates import get_business_day_of_month

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
    last_report = last_stock_on_hand(facility)
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
def lead_time(supply_point, month=None, year=None):
    ltime = calc_lead_time(supply_point, month=month, year=year)
    return render_to_string("tanzania/partials/lead_time.html", 
                            {"lead_time": ltime})
    
@register.simple_tag
def average_lead_time(supply_point_list, year=None, month=None):
    total_time = timedelta(days=0)
    count = 0
    for supply_point in supply_point_list:
        ltime = calc_lead_time(supply_point, year, month)
        if ltime is not None:
            total_time += ltime
            count += 1
    average_time = total_time / count if count else None
    return render_to_string("tanzania/partials/lead_time.html", 
                            {"lead_time": average_time})
    
@register.simple_tag
def last_report_elem(elem, supply_point, year, month, format=True):
    cell_template = '<%(elem)s class="%(classes)s">%(msg)s</%(elem)s>'
    state = soh_reported_on_time(supply_point, year, month)
    classes = "insufficient_data"
    msg = _("Waiting for reply")
    if state == OnTimeStates.NO_DATA or state == OnTimeStates.INSUFFICIENT_DATA:
        if format:
            return cell_template % {"classes": classes, "msg": msg, "elem": elem}
        else:
            return msg

    # check from business day to business day
    last_bd_of_the_month = get_business_day_of_month(year, month, -1)
    last_report = last_stock_on_hand_before(supply_point, last_bd_of_the_month)
    msg = defaultfilters.date(last_report.report_date, "d M Y")

    if not format: return msg

    if state == OnTimeStates.LATE:
        classes = "warning_icon iconified"
    elif state == OnTimeStates.ON_TIME:
        classes = "good_icon iconified"

    return cell_template % {"classes": classes, "msg": msg, "elem": elem}

last_report_cell = register.simple_tag(curry(last_report_elem, "td"))
last_report_span = register.simple_tag(curry(last_report_elem, "span"))


@register.simple_tag
def latest_note(supply_point):
    notes = SupplyPointNote.objects.filter(supply_point=supply_point).order_by("-date")
    if notes.count():
        return notes[0]
    return None

@register.simple_tag
def delivery_group(supply_point):
    group = supply_point.groups.all()[0].code \
            if supply_point and supply_point.groups.exists() else None
    if group:
        return "%s: %s" %(_("Delivery Group"), group)
    
    
@register.simple_tag
def on_time_percentage(facs, year, month):
    return float(len(soh_on_time_reporting(facs, year, month))) / float(len(facs))

@register.simple_tag
def soh_historical_response(facility):
    r = historical_response_rate(facility, SupplyPointStatusTypes.SOH_FACILITY)
    return "<span title='%d of %d'>%s%%</span>" % (r[1], r[2], floatformat(r[0]*100.0)) if r else "No data"

@register.simple_tag
def reverse_url_string(url):
    return reverse(url)