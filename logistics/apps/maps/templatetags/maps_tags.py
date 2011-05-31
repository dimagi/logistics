from django import template
from django.conf import settings
from django.template.loader import render_to_string

register = template.Library()

@register.simple_tag
def get_map_icon(supply_point, request):
    """
    Get a custom map icon based on the supply points stock information.
    Used in maps.
    """
    # arbitrary categorization
    # if no stock info, blank
    # if >= 50% products with stock good
    # if < 50% products with stock, bad
    count = supply_point.productstock_set.count() 
    if count == 0:
        icon = "no_data.png"
    elif supply_point.productstock_set.filter(quantity__gt=0).count() >= \
         supply_point.productstock_set.filter(quantity=0).count():
        icon = "good.png"
    else:
        icon = "bad.png"
    return "%s%s%s" % (settings.MEDIA_URL, "maps/icons/", icon) 
                     
@register.simple_tag
def get_map_popup(supply_point, request):
    return render_to_string("maps/partials/supply_point_popup.html", 
                            {"sp": supply_point}).replace("\n", "")
    