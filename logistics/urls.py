from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    # Django URLs
    (r'^admin/', include(admin.site.urls)),
    
    # RapidSMS core URLs
    (r'^rapidsms/', include('rapidsms.urls.login_logout')),
    url(r'^$', 'rapidsms.views.dashboard', name='rapidsms-dashboard'),

    # RapidSMS contrib app URLs
    (r'^ajax/', include('rapidsms.contrib.ajax.urls')),
    (r'^export/', include('rapidsms.contrib.export.urls')),
    (r'^httptester/', include('rapidsms.contrib.httptester.urls')),
    (r'^locations/', include('rapidsms.contrib.locations.urls')),
    (r'^ewsghana/', include('logistics.apps.ewsghana.urls')),
    (r'^messagelog/', include('rapidsms.contrib.messagelog.urls')),
    (r'^messaging/', include('rapidsms.contrib.messaging.urls')),

    # 3rd party django app URLs
    (r'^accounts/', include('registration.urls')),

    # other app URLS
    (r'^', include('logistics.apps.web_registration.urls')),
    (r'^registration/', include('logistics.apps.registration.urls')),
    (r'^logistics/', include('logistics.apps.logistics.urls')),
    (r'^reports/', include('logistics.apps.reports.urls')),
    (r'^scheduler/', include('rapidsms.contrib.scheduler.urls')),
    (r'^', include('auditcare.urls')),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        # helper URLs file that automatically serves the 'static' folder in
        # INSTALLED_APPS via the Django static media server (NOT for use in
        # production)
        (r'^', include('rapidsms.urls.static_media')),
    )
