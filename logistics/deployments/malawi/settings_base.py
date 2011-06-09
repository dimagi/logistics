# you should configure your database here before doing any real work.
# see: http://docs.djangoproject.com/en/dev/ref/settings/#databases

APPS = [
    "auditcare",
    "django.contrib.webdesign",
    "logistics.apps.malawi",
]

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'auditcare.middleware.AuditMiddleware',
    'logistics.apps.ewsghana.middleware.RequireLoginMiddleware',
)

# this rapidsms-specific setting defines which views are linked by the
# tabbed navigation. when adding an app to INSTALLED_APPS, you may wish
# to add it here, also, to expose it in the rapidsms ui.
RAPIDSMS_TABS = [
    ("logistics.apps.malawi.views.dashboard",       "Dashboard"),
    ("logistics.apps.malawi.views.facilities",       "Facilities"),
    ("logistics.apps.malawi.views.hsas",       "HSAs"),
    ("logistics.apps.malawi.views.help",       "Help"),
    ("logistics.apps.malawi.views.contacts",       "Management", "is_superuser"),
    ("logistics.apps.malawi.views.monitoring",       "M & E", "is_superuser"),
    ("registration",                          "Registration", "is_superuser"),
    ("rapidsms.contrib.messagelog.views.message_log",       "Message Log", "is_superuser"),
    ("rapidsms.contrib.httptester.views.generate_identity", "Message Tester", "is_superuser"),
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
    # zain modem (?)
    "modem": {
        "ENGINE": "logistics.backends.kannel",
        "host": "127.0.0.1",
        "port": 8002,
        "sendsms_url": "http://127.0.0.1:13013/cgi-bin/sendsms",
        "sendsms_params": {"smsc": "zain-modem",
                           "from": "+265992961466", # will be overridden; set for consistency
                           "username": "rapidsms",
                           "password": "CHANGEME"}, # set password in localsettings.py
        "coding": 0,
        "charset": "ascii",
        "encode_errors": "ignore", # strip out unknown (unicode) characters
    },
    # tnm smpp (?)
     "tnm-smpp": {
        "ENGINE": "logistics.backends.kannel",
        "host": "127.0.0.1",
        "port": 8003,
        "sendsms_url": "http://127.0.0.1:13013/cgi-bin/sendsms",
        "sendsms_params": {"smsc": "tnm-smpp",
                           "from": "2222", # not set automatically by SMSC
                           "username": "rapidsms",
                           "password": "CHANGEME"}, # set password in localsettings.py
        "coding": 0,
        "charset": "ascii",
        "encode_errors": "ignore", # strip out unknown (unicode) characters
    },
    # tester
    "message_tester": {
        "ENGINE": "rapidsms.backends.bucket",
    },
    # tester
    "message_tester": {
        "ENGINE": "rapidsms.backends.bucket",
    },
    # twilio
    "twilio": {
        "ENGINE": "rtwilio.backend",
        'host': 'localhost', 'port': '8081', # used for spawned backend WSGI server
        'config': {
            'account_sid': 'CHANGEME',
            'auth_token': 'CHANGEME',
            'number': '(###) ###-####',
            'callback': 'http://cstock.dimagi.com/twilio/status-callback/', # optional callback URL
        }
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

DEFAULT_RESPONSE = "Sorry, I could not understand your message. Please contact your supervisor for help."
COUNTRY = "malawi"
TIME_ZONE="Africa/Maputo"
COUNTRY_DIALLING_CODE = 265

import os
filedir = os.path.dirname(__file__)
STATIC_LOCATIONS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))), "static", "malawi", "health_centers.csv")
STATIC_PRODUCTS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))), "static", "malawi", "products.csv")

# change to not make product reports "active" by default
# should be True for Malawi, False for Ghana
LOGISTICS_LANDING_PAGE_VIEW = "malawi_dashboard"
LOGISTICS_USE_STATIC_EMERGENCY_LEVELS = True
LOGISTICS_DEFAULT_PRODUCT_ACTIVATION_STATUS = True
LOGISTICS_REORDER_LEVEL_IN_MONTHS = 1
LOGISTICS_MAXIMUM_LEVEL_IN_MONTHS = 2
LOGISTICS_AGGRESSIVE_SOH_PARSING = False
LOGISTICS_GHANA_HACK_CREATE_SCHEDULES = False
LOGISTICS_EXCEL_EXPORT_ENABLED = False
LOGISTICS_LOGIN_TEMPLATE = "malawi/login.html"
LOGISTICS_LOGOUT_TEMPLATE = "malawi/loggedout.html"
LOGISTICS_USE_AUTO_CONSUMPTION = True

LOGO_LEFT_URL="/static/malawi/images/malawi-flag.jpg"
LOGO_RIGHT_URL="/static/malawi/images/jsi_logo.png"
SITE_TITLE="cStock"
BASE_TEMPLATE="malawi/base.html"
BASE_TEMPLATE_SPLIT_2="malawi/base-split-2.html"

LOGISTICS_CONFIG = 'static.malawi.config'

LOGISTICS_ALERT_GENERATORS = [
    'logistics.apps.malawi.alerts.hsas_no_supervision',
    'logistics.apps.malawi.alerts.hsas_no_products',
    'logistics.apps.malawi.alerts.late_reporting_receipt',
    'logistics.apps.malawi.alerts.non_reporting_hsas',
    'logistics.apps.malawi.alerts.health_center_stockout',
    'logistics.apps.malawi.alerts.hsa_below_emergency_quantity',
    'logistics.apps.malawi.alerts.health_center_unable_resupply_stockout',
    'logistics.apps.malawi.alerts.health_center_unable_resupply_emergency',
]
