# you should configure your database here before doing any real work.
# see: http://docs.djangoproject.com/en/dev/ref/settings/#databases
import os
LOGISTICS_CONFIG = 'logistics_project.apps.tanzania.config'

APPS = [
    "auditcare",
    "django.contrib.webdesign",
    # commented out until fixed
    #"logistics_project.apps.ilsgateway",
    "logistics_project.apps.tanzania",
]

RAPIDSMS_TABS = [
    ("logistics_project.apps.tanzania.views.dashboard",       "Dashboard"),
#    ("logistics_project.apps.malawi.views.facilities",       "Facilities"),
#    ("logistics_project.apps.malawi.views.hsas",       "HSAs"),
#    ("logistics_project.apps.malawi.views.help",       "Help"),
#    ("logistics_project.apps.malawi.views.contacts",       "Management", "is_superuser"),
#    ("logistics_project.apps.malawi.views.monitoring",       "M & E", "is_superuser"),
#    ("registration",                          "Registration", "is_superuser"),
    ("rapidsms.contrib.messagelog.views.message_log",       "Message Log", "is_superuser"),
    ("rapidsms.contrib.httptester.views.generate_identity", "Message Tester", "is_superuser"),
]

INSTALLED_BACKENDS = {
    # tester
    "message_tester": {
        "ENGINE": "rapidsms.backends.bucket",
    },
}

# for postgresql:
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "ilsgateway",
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
COUNTRY = "tanzania"
TIME_ZONE="Africa/Maputo"
COUNTRY_DIALLING_CODE = 265

LANGUAGES = (
  ('sw', 'Swahili'),
  ('en', 'English'),
)

# change to not make product reports "active" by default
# should be True for Malawi, False for Ghana
LOGISTICS_LANDING_PAGE_VIEW = "tz_dashboard"
LOGISTICS_USE_STATIC_EMERGENCY_LEVELS = True
LOGISTICS_DEFAULT_PRODUCT_ACTIVATION_STATUS = True
LOGISTICS_REORDER_LEVEL_IN_MONTHS = 1
LOGISTICS_MAXIMUM_LEVEL_IN_MONTHS = 2
LOGISTICS_AGGRESSIVE_SOH_PARSING = False
LOGISTICS_GHANA_HACK_CREATE_SCHEDULES = False
LOGISTICS_EXCEL_EXPORT_ENABLED = False
LOGISTICS_LOGIN_TEMPLATE = "logistics/login.html"
LOGISTICS_LOGOUT_TEMPLATE = "logistics/loggedout.html"
LOGISTICS_USE_AUTO_CONSUMPTION = True
LOGISTICS_APPROVAL_REQUIRED = True
LOGISTICS_USE_COMMODITY_EQUIVALENTS = False

LOGO_LEFT_URL="/static/malawi/images/moh_logo.png"
LOGO_RIGHT_URL="/static/tanzania/img/TZ-Ministry-logo.gif"
SITE_TITLE="ILSGateway"
BASE_TEMPLATE="tanzania/base.html"
BASE_TEMPLATE_SPLIT_2="logistics/base-split-2.html"

LOGISTICS_ALERT_GENERATORS = [
    #'logistics_project.apps.malawi.alerts.hsa_below_emergency_quantity',
    #'logistics_project.apps.malawi.alerts.health_center_unable_resupply_stockout',
    #'logistics_project.apps.malawi.alerts.health_center_unable_resupply_emergency',
]


STATIC_LOCATIONS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))), "static", "tanzania", "migration", "all_facilities.csv")
