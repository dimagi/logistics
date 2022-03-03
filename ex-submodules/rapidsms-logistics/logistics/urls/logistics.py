from django.conf.urls import *

urlpatterns = patterns('',
    url(r'^no_ie_allowed/?$', 'logistics.views.no_ie_allowed', 
        name="no_ie_allowed"),
    url(r'^global_stats',
        'logistics.views.global_stats',
        name="global_stats")
)
