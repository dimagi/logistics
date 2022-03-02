from django.conf.urls import *

urlpatterns = patterns('',
    url(r'^no_ie_allowed/?$', 'logistics.views.no_ie_allowed', 
        name="no_ie_allowed"),
    # ok, so this isn't the most generic, but we don't yet know what the final dashboard will look like
    # so we'll use this as a placeholder until we do
    url(r'^dashboard/(?P<location_code>[\w-]+)/?$',
        'logistics.views.dashboard',
        name="logistics_dashboard"),
    url(r'^by_product/(?P<location_code>[\w-]+)/?$',
        'logistics.views.facilities_by_product',
        name="by_product"),
    url(r'^navigate$',
        'logistics.views.navigate',  
        name="navigate"),
    url(r'^messages_by_carrier$',
        'logistics.views.messages_by_carrier',
        name="messages_by_carrier"),
    url(r'^global_stats',
        'logistics.views.global_stats',
        name="global_stats")
)
