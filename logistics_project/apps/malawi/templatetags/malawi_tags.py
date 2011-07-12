from django import template
from django.core.urlresolvers import reverse
from rapidsms.contrib.messagelog.models import Message
from logistics.tables import ShortMessageTable
from logistics.util import config
from malawi.util import hsas_below

register = template.Library()

@register.simple_tag
def place_url(location):
    if location.type.slug == config.LocationCodes.HSA:
        return reverse("malawi_hsa", args=[location.code])
    elif location.type.slug == config.LocationCodes.FACILITY:
        return reverse("malawi_facility", args=[location.code])
    elif location.type.slug == config.LocationCodes.DISTRICT:
        return "%s?place=%s" % (reverse("malawi_facilities"), location.code)
    else:
        return reverse("malawi_dashboard")


@register.simple_tag
def breadcrumbs(location):
    mycrumbs = '<a href="%(link)s">%(display)s</a>' % \
                {"link": place_url(location),
                 "display": location.name}
    if location.parent is not None:
        # > 
        return '%(parentcrumbs)s &raquo; %(mycrumbs)s' % \
            {"parentcrumbs": breadcrumbs(location.parent),
             "mycrumbs": mycrumbs}
    else:
        return mycrumbs
    
@register.simple_tag
def product_availability_summary(location):
    if not location:
        pass # TODO: probably want to disable this if things get slow
        #return '<p class="notice">To view the product availability summary, first select a district.</p>'
    
    hsas = hsas_below(location)
    summary = ProductAvailabilitySummary(hsas)
    return _r_2_s_helper("logistics/partials/product_availability_summary.html", 
                         {"summary": summary})

@register.simple_tag
def recent_messages(contact, limit=5):
    # shouldn't this be ordered by something?
    return ShortMessageTable(Message.objects.filter(contact=contact, direction="I")[:limit]).as_html()
