# Copyright 2009, EveryBlock
# This code is released under the GPL.

from django.core.cache import cache
from django.template import Template
from django.template.context import RequestContext
from rapidsms.conf import settings
import urllib

class CachedTemplateMiddleware(object):
    """ The purpose of this middleware is to allow a double-render of the template
    so that we can easily have part of the page come from cache and part not 
    using templatetags and ignoring spot caching"""
    def process_view(self, request, view_func, view_args, view_kwargs):
        response = None
        if request.method == 'GET':
            cache_key = urllib.quote(request.path)
            response = cache.get(cache_key, None)

        if response is None:
            response = view_func(request, *view_args, **view_kwargs)

        if response['content-type'].startswith('text/html'):
            t = Template(response.content)
            response.content = t.render(RequestContext(request))

        return response
