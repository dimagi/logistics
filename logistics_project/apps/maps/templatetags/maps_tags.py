from django import template
from django.conf import settings
from django.template.loader import render_to_string
from logistics_project.utils.modules import to_function

register = template.Library()

@register.simple_tag
def get_map_icon(supply_point, request):
    """
    Get a custom map icon based on the supply points stock information.
    Used in maps.
    """
    if supply_point.data_unavailable():
        icon = "no_data.png"
    elif supply_point.productstock_set.filter(quantity__gt=0).count() <= \
         supply_point.productstock_set.filter(quantity=0).count():
        # if less in stock then out of stock, display warning
        icon = "stockout.png"
    elif supply_point.productstock_set.filter(quantity=0).count() > 0:
        # if there are *any* stockouts, display a warning
        icon = "warning.png"
    else:
        # if everything is good, display good
        icon = "goodstock.png"
    return "%s%s%s" % (settings.MEDIA_URL, "logistics/images/", icon) 

@register.simple_tag
def get_map_popup(supply_point, request):
    
    func = to_function(settings.LOGISTICS_MAP_POPUP_FUNCTION) \
            if hasattr(settings, "LOGISTICS_MAP_POPUP_FUNCTION") \
            else None
                
    if func:
        return func(supply_point, request)
    
    return render_to_string("maps/partials/supply_point_popup.html", 
                            {"sp": supply_point, 
                             "productstocks": supply_point.productstock_set.all().order_by('product__name')}
                            ).replace("\n", "")
