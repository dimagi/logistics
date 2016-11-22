from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin
from logistics_project.apps.ewsghana.views import redirect_view

admin.autodiscover()

urlpatterns = patterns('')

if settings.DEBUG:
    urlpatterns += patterns('',
        # helper URLs file that automatically serves the 'static' folder in
        # INSTALLED_APPS via the Django static media server (NOT for use in
        # production)
        (r'^', include('rapidsms.urls.static_media')),
    )

urlpatterns += patterns('',
    (r'^backdoor/', include('backdoor_urls')),
    (r'^.*', redirect_view)
)
