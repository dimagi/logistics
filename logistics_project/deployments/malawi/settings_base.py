# you should configure your database here before doing any real work.
# see: http://docs.djangoproject.com/en/dev/ref/settings/#databases

APPS = [
    "auditcare",
    "couchlog",
    "django.contrib.webdesign",
    "logistics_project.apps.malawi",
    "scheduler",
    "warehouse"
]

MIDDLEWARE_CLASSES = [
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'auditcare.middleware.AuditMiddleware',
    'logistics_project.apps.ewsghana.middleware.RequireLoginMiddleware',
#    'johnny.middleware.CommittingTransactionMiddleware',
#    'johnny.middleware.QueryCacheMiddleware',
]

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
        'OPTIONS': {
            'MAX_ENTRIES': 10000
        }
    }
}
CACHE_BACKEND = 'memcached://127.0.0.1:11211/'

#CACHE_BACKEND = 'johnny.backends.memcached://127.0.0.1:11211/'


# this rapidsms-specific setting defines which views are linked by the
# tabbed navigation. when adding an app to INSTALLED_APPS, you may wish
# to add it here, also, to expose it in the rapidsms ui.

RAPIDSMS_TABS = [
    ("logistics_project.apps.malawi.warehouse.views.dashboard", "Dashboard", None, "/malawi/r/dashboard/"),
    ("logistics_project.apps.malawi.warehouse.views.hsas", "HSAs", None, "/malawi/r/hsas/"),
    ("logistics_project.apps.malawi.warehouse.views.health_facilities", "Health Facilities", None, "/malawi/r/health-facilities/"),
    ("logistics_project.apps.malawi.warehouse.views.user_profiles", "User Profiles", None, "/malawi/r/user-profiles/"),    
    ("logistics_project.apps.malawi.views.monitoring",       "M & E", "auth.admin_read"),
    ("rapidsms.contrib.messagelog.views.message_log", "Message Log", "auth.admin_read"),
    ("rapidsms.contrib.httptester.views.generate_identity", "Message Tester", "is_superuser"),
    ("rapidsms.contrib.messagelog.views.contacts", "Management", "is_superuser", "/malawi/management/"),
    ("logistics_project.apps.malawi.views.help", "Help"),
]

from django.utils.datastructures import SortedDict

REPORT_LIST = SortedDict([
    ("Reporting Rate", "reporting-rate"),
    ("Stock Status", "stock-status"),
    ("Consumption Profiles", "consumption-profiles"),
    ("Alert Summary", "alert-summary"),
    ("Re-supply Qts Required", "re-supply-qts-required"),
    ("Lead Times", "lead-times"),
    ("Order Fill Rate", "order-fill-rate"),
    ("Emergency Orders", "emergency-orders"),
])

REPORT_FOLDER = "malawi/new/reports"
MANAGEMENT_FOLDER = "malawi/new/management"

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
    "airtel-smpp": {
        "ENGINE": "rapidsms.backends.kannel",
        "host": "127.0.0.1",
        "port": 8002,
        "sendsms_url": "http://127.0.0.1:13013/cgi-bin/sendsms",
        "sendsms_params": {"smsc": "airtel-smpp",
                           "from": "56543", # not set automatically by SMSC
                           "username": "rapidsms",
                           "password": "CHANGEME"}, # set password in localsettings.py
        "coding": 0,
        "charset": "ascii",
        "encode_errors": "ignore", # strip out unknown (unicode) characters
    },
    # tnm smpp (?)
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
STATIC_RESOURCES = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))), "logistics_project", "apps", "malawi", "static", "resources")

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
LOGISTICS_LOGOUT_TEMPLATE = "logistics/loggedout.html"
LOGISTICS_USE_AUTO_CONSUMPTION = True
LOGISTICS_APPROVAL_REQUIRED = False
LOGISTICS_USE_COMMODITY_EQUIVALENTS = False
LOGISTICS_USERS_HAVE_ADMIN_ACCESS = True
LOGISTICS_DAYS_UNTIL_LATE_PRODUCT_REPORT = 2
LOGISTICS_REPORTING_CYCLE_IN_DAYS = 30

LOGISTICS_CONSUMPTION = {
    "MINIMUM_TRANSACTIONS": 2,
    "MINIMUM_DAYS": 10,
    "LOOKBACK_DAYS": 60,            
    "INCLUDE_END_STOCKOUTS": True, 
}


SESSION_EXPIRE_AT_BROWSER_CLOSE=True

LOGO_LEFT_URL="/static/malawi/images/moh_logo.png"
LOGO_RIGHT_URL="/static/malawi/images/jsi_logo.png"
SITE_TITLE="cStock"
BASE_TEMPLATE="malawi/base.html"
BASE_TEMPLATE_SPLIT_2="logistics/base-split-2.html"

LOGISTICS_CONFIG = 'static.malawi.config'

LOGISTICS_ALERT_GENERATORS = [
    #'logistics_project.apps.malawi.alerts.hsas_no_supervision',
    #'logistics_project.apps.malawi.alerts.hsas_no_products',
    #'logistics_project.apps.malawi.alerts.late_reporting_receipt',
    #'logistics_project.apps.malawi.alerts.non_reporting_hsas',
    #'logistics_project.apps.malawi.alerts.health_center_stockout',
    'logistics_project.apps.malawi.alerts.hsa_below_emergency_quantity',
    'logistics_project.apps.malawi.alerts.health_center_unable_resupply_stockout',
    'logistics_project.apps.malawi.alerts.health_center_unable_resupply_emergency',
]

CONTACT_GROUP_GENERATORS = [
#    "groupmessaging.views.all_contacts",
    "groupmessaging.views.all_contacts_with_all_backends",
    "groupmessaging.views.all_contacts_with_all_roles",
    "logistics_project.apps.malawi.message_groups.by_district",
    "logistics_project.apps.malawi.message_groups.by_facility",
]

DATABASE_ENGINE = "mysql"


SOUTH_MIGRATION_MODULES = {
    'rapidsms': 'logistics_project.deployments.malawi.migrations.rapidsms',
    # NOTE: can't fix this without breaking tests and/or doing a major 
    # migration dependency cleanup
    #'logistics': 'ignore', 
    #'logistics': 'logistics_project.deployments.malawi.migrations.logistics',
    'logistics': 'logistics_project.deployments.malawi.migrations.logistics',
    # 'malawi': 'ignore'
}

# data warehouse config
WAREHOUSE_RUNNER = 'logistics_project.apps.malawi.warehouse.runner.MalawiWarehouseRunner'
