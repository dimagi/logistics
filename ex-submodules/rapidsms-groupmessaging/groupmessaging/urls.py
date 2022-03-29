from __future__ import unicode_literals
from django.conf.urls import *
from . import views

urlpatterns = [
    url(r'^blast/?$', views.group_message, name="group_message"),
    url(r'^ajax_contact_count', views.ajax_contact_count, name="ajax_contact_count")
]
