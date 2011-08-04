# you should configure your database here before doing any real work.
# see: http://docs.djangoproject.com/en/dev/ref/settings/#databases
import os
LOGISTICS_CONFIG = 'logistics.apps.tanzania.config'

APPS = [
    "auditcare",
    "django.contrib.webdesign",
    # commented out until fixed
    #"logistics.apps.ilsgateway",
    "logistics.apps.tanzania",
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
LOGISTICS_APPROVAL_REQUIRED = True
LOGISTICS_USE_COMMODITY_EQUIVALENTS = False

SESSION_EXPIRE_AT_BROWSER_CLOSE=True

LOGO_LEFT_URL="/static/malawi/images/moh_logo.png"
LOGO_RIGHT_URL="/static/malawi/images/jsi_logo.png"
SITE_TITLE="cStock"
BASE_TEMPLATE="malawi/base.html"
BASE_TEMPLATE_SPLIT_2="malawi/base-split-2.html"

LOGISTICS_ALERT_GENERATORS = [
    #'logistics.apps.malawi.alerts.hsa_below_emergency_quantity',
    #'logistics.apps.malawi.alerts.health_center_unable_resupply_stockout',
    #'logistics.apps.malawi.alerts.health_center_unable_resupply_emergency',
]


STATIC_REGIONS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))), "logistics", "apps", "tanzania", "fixtures", "regions.csv")
STATIC_DISTRICTS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))), "logistics", "apps", "tanzania", "fixtures", "districts.csv")
STATIC_FACILITIES = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))), "logistics", "apps", "tanzania", "fixtures", "facilities.csv")
