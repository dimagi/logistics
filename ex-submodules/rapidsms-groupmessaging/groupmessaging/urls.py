from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^$',
        "groupmessaging.views.group_message",
        name="group_message"),
    url(r'^/ajax_contact_count',
        "groupmessaging.views.ajax_contact_count",
        name="ajax_contact_count"
    )
)
