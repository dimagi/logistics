from __future__ import unicode_literals
from django.urls import path
from . import views

urlpatterns = [
    path('', views.message_log, name="message_log"),
]
