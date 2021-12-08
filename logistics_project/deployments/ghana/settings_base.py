# you should configure your database here before doing any real work.
# see: http://docs.djangoproject.com/en/dev/ref/settings/#databases

APPS = [
    "rapidsms.contrib.scheduler",
    "logistics_project.apps.ewsghana",
    "logistics_project.apps.smsgh",
]

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'logistics_project.apps.ewsghana.middleware.RequireLoginMiddleware',
)

# this rapidsms-specific setting defines which views are linked by the
# tabbed navigation. when adding an app to INSTALLED_APPS, you may wish
# to add it here, also, to expose it in the rapidsms ui.
RAPIDSMS_TABS = [
    ("aggregate_ghana",                                     "Stock Levels"),
    ("ewsghana_reporting",                                  "Usage"),
    ("district_dashboard",                                  "District Dashboard"),
    #("input_stock",                                        "Input Stock"),
    ("ewsghana_scheduled_reports",                          "Configuration"),
    #("email_reports",                                      "Email Reports"),
    ("help",                                                "Help"),
    #("rapidsms.contrib.messaging.views.messaging",         "Messaging"),
    #("rapidsms.contrib.locations.views.locations",         "Map"),
    #("rapidsms.contrib.scheduler.views.index",             "Event Scheduler"),
    ("rapidsms.contrib.httptester.views.generate_identity", "Message Tester"),
    ("maps_dashboard",                                      "Maps"),
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
        "ENGINE": "rapidsms.backends.smsgh_http",
        "PORT": 8002,
        "HOST": "localhost",
        "gateway_url" : "http://localhost",
        #"gateway_url" : "http://127.0.0.1:8080",
        "params_outgoing": "user=my_username&snr=%2B&password=my_password&id=%(phone_number)s&text=%(message)s",
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

DJANGO_LOG_FILE = "logistics.django.log"
LOG_SIZE = 1000000
LOG_LEVEL   = "DEBUG"
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

LOGISTICS_AGGRESSIVE_SOH_PARSING = True
LOGISTICS_MINIMUM_DAYS_TO_CALCULATE_CONSUMPTION = 60
LOGISTICS_USE_COMMODITY_EQUIVALENTS = True
LOGISTICS_CONFIG = 'static.ghana.config'

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
    'logistics_project.apps.ewsghana.alerts.consumption_not_set',
    'logistics.alerts.facilities_without_reminders',
    'logistics_project.apps.ewsghana.alerts.contact_without_phone',
]

DEFAULT_BACKEND='message_tester'
DEBUG=True
