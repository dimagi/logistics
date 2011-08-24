from django import template
from django.conf import settings
from logistics.util import config
import logging

register = template.Library()

def _url_generator():
    if hasattr(settings, "LOGISTICS_URL_GENERATOR_FUNCTION"):
        try:
            # TODO: make this less brittle if imports or args don't line up
            module, callback = settings.LOGISTICS_URL_GENERATOR_FUNCTION.rsplit(".", 1)
            module = __import__(module, globals(), locals(), [callback])
            callback = getattr(module, callback)
            return callback
        except ImportError:
            logging.error("problem importing url function %s" % settings.LOGISTICS_URL_GENERATOR_FUNCTION)
    
        
@register.simple_tag
def breadcrumbs(location, url_generator=None):
    if location is None: return ""
    if url_generator is None: 
        url_generator = _url_generator()
    
    if url_generator is not None:
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
    
