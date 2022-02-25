from django.conf.urls import *

urlpatterns = patterns('alerts.ajax',
    url(r'^ajax/addcomment/$', 'add_comment'),
    url(r'^ajax/alertaction/$', 'alert_action'),
)
