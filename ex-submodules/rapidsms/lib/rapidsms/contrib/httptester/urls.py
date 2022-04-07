from __future__ import unicode_literals
from django.urls import path, re_path
from . import views


urlpatterns = [
    path('', views.generate_identity, name='rapidsms_message_tester_default'),
    re_path(r"^(?P<identity>[+]?\d+)/$", views.message_tester),
]
