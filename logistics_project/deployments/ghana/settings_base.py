# you should configure your database here before doing any real work.
# see: http://docs.djangoproject.com/en/dev/ref/settings/#databases

TEMPLATE_DIRS = [
    "templates", 
]

APPS = [
    "auditcare",
    "couchlog",
    "rapidsms.contrib.scheduler",
    "logistics_project.apps.ewsghana",
    "logistics_project.apps.smsgh",
    "rapidsms.contrib.messaging",
    "soil",
    "django.contrib.comments",
]

MIDDLEWARE_CLASSES = [
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'auditcare.middleware.AuditMiddleware',
    'logistics_project.apps.ewsghana.middleware.AutoLogout',
    'logistics_project.apps.ewsghana.middleware.RequireLoginMiddleware',
    'logistics.middleware.CachedTemplateMiddleware',
]

# this rapidsms-specific setting defines which views are linked by the
# tabbed navigation. when adding an app to INSTALLED_APPS, you may wish
# to add it here, also, to expose it in the rapidsms ui.
RAPIDSMS_TABS = [
    ("aggregate",                                           "Stock Levels"),
    ("ewsghana_reporting",                                  "Usage"),
    ("district_dashboard",                                  "Dashboard"),
    #("input_stock",                                        "Input Stock"),
    ("ewsghana_scheduled_reports",                          "Configuration"),
    #("email_reports",                                      "Email Reports"),
    ("help",                                                "Help"),
    #("rapidsms.contrib.messaging.views.messaging",         "Messaging"),
    #("rapidsms.contrib.locations.views.locations",         "Map"),
    #("rapidsms.contrib.scheduler.views.index",             "Event Scheduler"),
    ("rapidsms.contrib.httptester.views.generate_identity", "Message Tester"),
    ("maps_dashboard",                                      "Maps"),
    ("group_message",                                       "Broadcast", "is_superuser"),
    ("ewsghana_comments",                                   "Comments"),
]

# the rapidsms backend configuration is designed to resemble django's
# database configuration, as a nested dict of (name, configuration).
#
# the ENGINE option specifies the module of the backend; the most common
# backend types (for a GSM modem or an SMPP server) are bundled with
# rapidsms, but you may choose to write your own.
#
# all other options are passed to the Backend when it is instantiated,
# to configure it. see the documentation in those modules for a list of
# the valid options for each.
INSTALLED_BACKENDS = {
#    "MTN": {
#        "ENGINE": "rapidsms.backends.gsm",
#        "PORT": "/dev/ttyUSB0",
#        "baudrate":115200,
#        "rtscts": 1
#    },
#    "end2end": {
#        "ENGINE": "rapidsms.backends.http",
#        "PORT": 8002,
#        "HOST": localhost,
#        "gateway_url" : "http://gw1.promessaging.com/sms.php",
#        "params_outgoing": "user=my_username&snr=%2B&password=my_password&id=%(phone_number)s&text=%(message)s",
#        "params_incoming": "snr=%(phone_number)s&msg=%(message)s"
#    },
    "smsgh": {
        "ENGINE": "logistics_project.backends.smsgh_http",
        "PORT": 8002,
        "HOST": "localhost",
        "gateway_url" : "http://localhost",
        #"gateway_url" : "http://127.0.0.1:8080",
        "params_outgoing": "user=my_username&snr=%2B&password=my_password&id=%(phone_number)s&text=%(message)s&from=%(from)s",
        "params_incoming": "snr=%(phone_number)s&msg=%(message)s"
    },
    "message_tester": {
        "ENGINE": "rapidsms.backends.bucket",
    },
}

# for postgresql:
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "logistics",
        "USER": "postgres",
        "PASSWORD": "test",
        "HOST": "localhost",
    }
}

TESTING_DATABASES= {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",#
        "NAME": "logistics.sqlite3",
    }
}

CACHES = {
    'default': {
        # In Django 1.3, looks like the DummyCache always returns None. lame. 
        #'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}

DJANGO_LOG_FILE = "logistics.django.log"
LOG_SIZE = 1000000
LOG_LEVEL   = "WARNING"
LOG_FILE    = "logistics.log"
LOG_FORMAT  = "[%(name)s]: %(message)s"
LOG_BACKUPS = 256 # number of logs to keep

DEFAULT_RESPONSE = "Sorry, I could not understand your message. Please contact your DHIO for help, or visit http://www.ewsghana.com"
COUNTRY = "ghana"
TIME_ZONE="Africa/Accra"
COUNTRY_DIALLING_CODE = 233

import os
filedir = os.path.dirname(__file__)
STATIC_LOCATIONS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))), "static", "ghana", "Facilities.csv")

LOGISTICS_LANDING_PAGE_VIEW = "ghana_dashboard"
LOGISTICS_LOGIN_TEMPLATE = "ewsghana/login.html"
LOGISTICS_LOGOUT_TEMPLATE = "ewsghana/loggedout.html"
LOGISTICS_AGGRESSIVE_SOH_PARSING = True
LOGISTICS_USE_AUTO_CONSUMPTION = True
LOGISTICS_USE_COMMODITY_EQUIVALENTS = True
LOGISTICS_CONFIG = 'static.ghana.config'
LOGISTICS_USE_SPOT_CACHING = True
LOGISTICS_SPOT_CACHE_TIMEOUT = 60*60
LOGISTICS_REPORTING_CYCLE_IN_DAYS = 7 
LOGISTICS_CONSUMPTION = {
    "MINIMUM_TRANSACTIONS": 2,
    "MINIMUM_DAYS": 60,
    "LOOKBACK_DAYS": None,          # none is no max
    "INCLUDE_END_STOCKOUTS": False, # whether or not to include periods ending in a stockout    
}
LOGISTICS_USE_GLOBAL_STOCK_LEVEL_POLICY = False
LOGISTICS_STOCKED_BY = 'facility'
LOGISTICS_USE_LOCATION_SESSIONS = True
LOGISTICS_NAVIGATION_MODE = "param" 

LOGO_LEFT_URL="/static/ewsghana/images/ghs_logo.png"
LOGO_RIGHT_URL=""
SITE_TITLE="Early Warning System"
BASE_TEMPLATE="ewsghana/base.html"
BASE_TEMPLATE_SPLIT_2="logistics/base-split-2.html"

# TODO: move this configuration over to urls.py
SMS_REGISTRATION_VIEW='ewsghana_sms_registration'
SMS_REGISTRATION_EDIT='ewsghana_registration_edit'

# some random place in the middle of ghana
MAP_DEFAULT_LATITUDE  = 6.55
MAP_DEFAULT_LONGITUDE = -1.2166667

LOGISTICS_ALERT_GENERATORS = [
    'logistics.alerts.non_reporting_facilities',
    'logistics.alerts.facilities_without_reporters',
    'logistics_project.apps.ewsghana.alerts.facilities_without_incharge',
    'logistics.alerts.facilities_without_reminders',
    'logistics_project.apps.ewsghana.alerts.contact_without_phone',
]

NOTIFICATION_ERROR_WEEKS = 4
LOGISTICS_NOTIF_GENERATORS = (
    'logistics_project.apps.ewsghana.notifications.missing_report_notifications',
    'logistics_project.apps.ewsghana.notifications.incomplete_report_notifications',
    'logistics_project.apps.ewsghana.notifications.stockout_notifications',
    'logistics_project.apps.ewsghana.notifications.urgent_stockout_notifications',
    'logistics_project.apps.ewsghana.notifications.urgent_nonreporting_notifications',
)

DEFAULT_BACKEND='message_tester'
DEBUG=True

SOUTH_MIGRATION_MODULES = {
    'rapidsms': 'deployments.ghana.migrations.rapidsms',
    'logistics': 'deployments.ghana.migrations.logistics',
    'ewsghana': 'deployments.ghana.migrations.ewsghana',
    'email_reports': 'deployments.ghana.migrations.email_reports',
    'locations': 'deployments.ghana.migrations.locations',
    'alerts': 'deployments.ghana.migrations.alerts',
}

AUTO_LOGOUT_DELAY = 300

CONTACT_GROUP_GENERATORS = [
    "groupmessaging.views.all_contacts_with_all_roles",
    "logistics_project.apps.ewsghana.message_groups.by_district",
    "logistics_project.apps.ewsghana.message_groups.by_facility",
]

CUSTOM_EXPORTS = [
    ("Web User Activity", "logistics_project.apps.ewsghana.tasks.export_auditor")
]
