from __future__ import unicode_literals
from django.conf.urls import *
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.views import login as django_login
from django.contrib.auth.views import logout as django_logout
from django.contrib.auth.views import password_change as django_password_change
from logistics_project.apps.malawi.warehouse.views import default_landing

admin.autodiscover()

urlpatterns = [
    # Django URLs
    url(r'^admin/', include(admin.site.urls)),
    
    url(r'^$', default_landing, name="rapidsms-dashboard"),

    # RapidSMS contrib app URLs
    url(r'^ajax/', include('rapidsms.contrib.ajax.urls')),
    url(r'^httptester/', include('rapidsms.contrib.httptester.urls')),
    url(r'^messagelog/', include('rapidsms.contrib.messagelog.urls')),

    url(r'^malawi/', include('logistics_project.apps.malawi.urls')),

    url(r'^group/', include('groupmessaging.urls')),

    # login/logout. this is order dependent
    url(r'^accounts/login/$', django_login, 
        kwargs={"template_name": "malawi/login.html"},
        name='rapidsms-login'),
    url(r'^accounts/logout/$', django_logout, 
        kwargs={"template_name": settings.LOGISTICS_LOGOUT_TEMPLATE},
        name='rapidsms-logout'),
    url(r'^accounts/password/change/$', django_password_change, 
        kwargs={"template_name": settings.LOGISTICS_PASSWORD_CHANGE_TEMPLATE,
                "post_change_redirect": settings.LOGIN_REDIRECT_URL },
        name='rapidsms-password-change'),
    
    # other app URLS
    url(r'^registration/', include('logistics_project.apps.registration.urls')),
]
