from __future__ import unicode_literals
from django.conf.urls import *
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.urls import path

from logistics_project.apps.malawi.warehouse.views import default_landing

admin.autodiscover()

urlpatterns = [
    # Django URLs
    path('admin/', admin.site.urls),
    
    url(r'^$', default_landing, name="rapidsms-dashboard"),

    # RapidSMS contrib app URLs
    url(r'^ajax/', include('rapidsms.contrib.ajax.urls')),
    url(r'^httptester/', include('rapidsms.contrib.httptester.urls')),
    url(r'^messagelog/', include('rapidsms.contrib.messagelog.urls')),

    url(r'^malawi/', include('logistics_project.apps.malawi.urls')),

    url(r'^group/', include('groupmessaging.urls')),

    # login/logout. this is order dependent
    url(r'^accounts/login/$', LoginView.as_view(template_name="malawi/login.html"),
        name='rapidsms-login'),
    url(r'^accounts/logout/$', LogoutView.as_view(template_name=settings.LOGISTICS_LOGOUT_TEMPLATE),
        name='rapidsms-logout'),
    url(r'^accounts/password/change/$',
        PasswordChangeView.as_view(template_name='logistics/password_reset_form.html',
                                   success_url='/'),
        name='password-change'),
    
    # other app URLS
    url(r'^registration/', include('logistics_project.apps.registration.urls')),
]
