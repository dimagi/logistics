from django import template
from django.conf import settings
from logistics.util import config
import logging
from dimagi.utils.modules import to_function

register = template.Library()

def _url_generator():
    if hasattr(settings, "LOGISTICS_URL_GENERATOR_FUNCTION"):
        return to_function(settings.LOGISTICS_URL_GENERATOR_FUNCTION)

@register.simple_tag
def breadcrumbs(location, url_generator=None):
    if location is None: return ""
    if url_generator is None: 
        url_generator = _url_generator()
    
    if url_generator is not None and url_generator(location):
        mycrumbs = '<a href="%(link)s">%(display)s</a>' % \
                    {"link": url_generator(location),
                     "display": location.name}
    else: 
        mycrumbs = location.name
    if location.parent is not None:
        return '%(parentcrumbs)s &raquo; %(mycrumbs)s' % \
            {"parentcrumbs": breadcrumbs(location.parent, url_generator),
             "mycrumbs": mycrumbs}
    else:
        return mycrumbs
    
