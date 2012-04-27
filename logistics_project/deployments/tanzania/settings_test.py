# this file has to exist for the build server 
from .settings_base import *

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'auditcare.middleware.AuditMiddleware',
    'logistics_project.apps.ewsghana.middleware.RequireLoginMiddleware',
    'django.middleware.locale.LocaleMiddleware',
#        'debug_toolbar.middleware.DebugToolbarMiddleware'
    )

INSTALLED_BACKENDS = {
    # tester
    "message_tester": {
        "ENGINE": "rapidsms.backends.bucket",
    },
    # message migration
    "migration": {
        "ENGINE": "logistics_project.apps.migration.backends.migration",
    },

    "push": {
        "ENGINE": "logistics_project.backends.push",
        'host': 'localhost', 'port': '8081', # used for spawned backend WSGI server
        'config': {
            'url': "http://127.0.0.1:9990/",
            'channel': "24358",
            'service': "147118",
            'password': 'CHANGEME',
        }
    },
}
