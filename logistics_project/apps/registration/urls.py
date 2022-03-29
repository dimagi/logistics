from __future__ import unicode_literals
from django.conf.urls import *
from . import views


urlpatterns = [
    url(r'^$', views.registration, name="registration"),
    url(r'^search$', views.search, name="search"),
    url(r'^(?P<pk>\d+)/edit$', views.registration, name="registration_edit"),
]
