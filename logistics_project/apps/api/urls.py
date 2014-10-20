from django.conf.urls.defaults import *
from django.http import HttpResponseNotFound
from tastypie.api import Api
from logistics_project.apps.api.resources import v0_1
from dimagi.utils.decorators import inline

API_LIST = (
    ((0, 1), (
        v0_1.ProductResources,
        v0_1.WebUserResources,
        v0_1.SMSUserResources,
        v0_1.LocationResources,
        v0_1.SupplyPointResources
    )),
)

class EWSApi(Api):
    def top_level(self, request, api_name=None, **kwargs):
        return HttpResponseNotFound()

@inline
def api_url_patterns():
    for version, resources in API_LIST:
        api = EWSApi(api_name='v%d.%d' % version)
        for R in resources:
            api.register(R())
        yield (r'^', include(api.urls))

urlpatterns = patterns('',
    *list(api_url_patterns))