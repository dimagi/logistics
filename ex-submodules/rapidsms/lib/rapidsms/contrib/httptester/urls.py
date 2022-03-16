from django.conf.urls import url
from . import views


urlpatterns = [
    url(r"^$", views.generate_identity, name='rapidsms_message_tester_default'),
    url(r"^(?P<identity>[+]?\d+)/$", views.message_tester),
]
