from django.conf.urls.defaults import *

urlpatterns = patterns('alerts.ajax',
    url(r'^ajax/addcomment/$', 'add_comment'),
    url(r'^ajax/alertaction/$', 'alert_action'),
)
