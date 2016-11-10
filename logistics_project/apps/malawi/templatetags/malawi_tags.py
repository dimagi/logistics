from django import template
from django.conf import settings
from logistics.util import config
from django.core.urlresolvers import reverse
from apps.malawi.util import hsas_below
from logistics.reports import ProductAvailabilitySummary
from logistics.templatetags.logistics_report_tags import r_2_s_helper
from rapidsms.templatetags.tabs_tags import Tab, TabsNode

register = template.Library()


class MalawiTab(Tab):
    pass


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
    return r_2_s_helper("logistics/partials/product_availability_summary.html", 
                         {"summary": summary})


@register.tag
def get_malawi_tabs(parser, token):
    """
    Modeled after rapidsms.templatetags.tabs_tags.get_tabs, only this
    version uses a different format for the RAPIDSMS_TABS setting and
    instantiates MalawiTab objects.

    Invoking this tag will instantiate all MalawiTab objects for the project
    and put them into the template context with the variable name given
    by context_varname.

    Syntax:
        {% get_malawi_tabs as [context_varname] %}

    Example:
        {% get_malawi_tabs as tabs %}

    All tabs should be defined in settings.RAPIDSMS_TABS, which is a list
    of (args, kwargs) tuples that get passed as args and kwargs to each
    MalawiTab upon instantiation.
    """

    args = token.contents.split()

    if len(args) != 3 or args[1] != "as":
        raise template.TemplateSyntaxError("Usage: {% get_malawi_tabs as [context_varname] %}")

    tabs = [
        MalawiTab(*tab_args, **tab_kwargs)
        for tab_args, tab_kwargs in settings.RAPIDSMS_TABS
    ]

    return TabsNode(tabs, args[2])
