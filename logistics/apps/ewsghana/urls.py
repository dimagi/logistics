#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.conf.urls.defaults import *
from rapidsms.contrib.messagelog.models import Message
from rapidsms.contrib.messagelog.views import message_log

urlpatterns = patterns('',
    url(r'^messagelog/export/$', 'django_tablib.views.export', {
        'model': Message}, name="export_messagelog"),
    url(r'^messagelog/$', message_log, {
        'template': 'ewsghana/messagelog.html'}, name="ewsghana_message_log")
)
