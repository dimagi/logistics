from django import template
from logistics.util import config
from django.core.urlresolvers import reverse

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