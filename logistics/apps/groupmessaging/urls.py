from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^$',
        "logistics.apps.groupmessaging.views.group_message",
        name="group_message"),
)
