from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.views import login as django_login
from django.contrib.auth.views import logout as django_logout
from django.contrib.auth.views import password_change as django_password_change

admin.autodiscover()

urlpatterns = patterns('',
    # Django URLs
    (r'^admin/', include(admin.site.urls)),
    
    # RapidSMS core URLs
    #(r'^rapidsms/', include('rapidsms.urls.login_logout')), # stolen by web_registration
    #url(r'^$', 'rapidsms.views.dashboard', name='rapidsms-dashboard'),
    url(r'^/?$', 'logistics.views.landing_page',
        name="rapidsms-dashboard"),

    # RapidSMS contrib app URLs
    (r'^ajax/', include('rapidsms.contrib.ajax.urls')),
    (r'^export/', include('rapidsms.contrib.export.urls')),
    (r'^httptester/', include('rapidsms.contrib.httptester.urls')),
    (r'^locations/', include('rapidsms.contrib.locations.urls')),
    (r'^messagelog/', include('rapidsms.contrib.messagelog.urls')),
    (r'^messaging/', include('rapidsms.contrib.messaging.urls')),

    # i guess having all of these is ok for now (?)    
    (r'^ewsghana/', include('logistics_project.apps.ewsghana.urls.ewsghana')),
    (r'^malawi/', include('logistics_project.apps.malawi.urls')),
    (r'^maps/', include('logistics_project.apps.maps.urls')),
    (r'^tz/', include('logistics_project.apps.tanzania.urls')),
    
    (r'^group/', include('groupmessaging.urls')),

    # login/logout. this is order dependent
    url(r'^accounts/login/$', django_login, 
        kwargs={"template_name": settings.LOGISTICS_LOGIN_TEMPLATE}, 
        name='rapidsms-login'),
    url(r'^accounts/logout/$', django_logout, 
        kwargs={"template_name": settings.LOGISTICS_LOGOUT_TEMPLATE},
        name='rapidsms-logout'),
    url(r'^accounts/password/change/$', django_password_change, 
        kwargs={"template_name": settings.LOGISTICS_PASSWORD_CHANGE_TEMPLATE,
                "post_change_redirect": settings.LOGIN_REDIRECT_URL },
        name='rapidsms-password-change'),
    
    # 3rd party django app URLs
    (r'^accounts/', include('registration.urls')),

    # other app URLS
    #(r'^', include('logistics_project.apps.web_registration.urls')), # stolen by ewsghana.urls
    (r'^registration/', include('logistics_project.apps.registration.urls')),
    (r'^logistics/', include('logistics.urls.logistics')),
    #(r'^logistics/', include('logistics.urls.config')), # stolen by ewsghana
    (r'^reports/', include('email_reports.urls')),
    (r'^scheduler/', include('rapidsms.contrib.scheduler.urls')),
    (r'^i18n/', include('django.conf.urls.i18n')),
)



if settings.DEBUG:
    urlpatterns += patterns('',
        # helper URLs file that automatically serves the 'static' folder in
        # INSTALLED_APPS via the Django static media server (NOT for use in
        # production)
        (r'^', include('rapidsms.urls.static_media')),
    )
