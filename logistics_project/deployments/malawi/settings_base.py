from __future__ import unicode_literals
# you should configure your database here before doing any real work.
# see: http://docs.djangoproject.com/en/dev/ref/settings/#databases
from collections import OrderedDict

PRIORITY_APPS = []

APPS = [
    "logistics_project.apps.malawi",
    "logistics_project.apps.outreach",
    "scheduler",
    "warehouse",
]

MIDDLEWARE = [
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'logistics_project.apps.malawi.middleware.RequireLoginMiddleware',
]

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://localhost:6379/0',
        'OPTIONS': {
        },
    },
}


# See logistics_project.apps.malawi.templatetags.malawi_tags.get_malawi_tabs

RAPIDSMS_TABS = [
    (("logistics_project.apps.malawi.warehouse.views.home", "Dashboard"),
     {"url": "/malawi/r/dashboard/", "applicable_base_levels": ["h"]}),

    (("logistics_project.apps.malawi.warehouse.views.facility_home", "Dashboard"),
     {"url": "/malawi/f/dashboard/", "applicable_base_levels": ["f"]}),

    (("logistics_project.apps.malawi.warehouse.views.hsas", "HSAs"),
     {"url": "/malawi/r/hsas/", "applicable_base_levels": ["h"]}),

    (("logistics_project.apps.malawi.warehouse.views.health_facilities", "Health Facilities"),
     {"url": "/malawi/r/health-facilities/", "applicable_base_levels": ["h"]}),

    (("logistics_project.apps.malawi.warehouse.views.user_profiles", "User Profiles"),
     {"url": "/malawi/r/user-profiles/", "applicable_base_levels": ["h"]}),

    (("malawi_monitoring", "M & E"),
     {"permission": "auth.admin_read", "applicable_base_levels": ["h"]}),

    (("message_log", "Message Log"),
     {"permission": "auth.admin_read", "applicable_base_levels": ["h", "f"]}),

    (("rapidsms_message_tester_default", "Message Tester"),
     {"permission": "is_superuser", "applicable_base_levels": ["h", "f"]}),

    (("malawi_management", "Management"),
     {"permission": "is_superuser", "url": "/malawi/management/", "applicable_base_levels": ["h", "f"]}),

    (("malawi_help", "Help"), {}),
]


REPORT_LIST = OrderedDict([
    ("Reporting Rate", "reporting-rate"),
    ("Stock Status", "stock-status"),
    ("Consumption Profiles", "consumption-profiles"),
    ("Alert Summary", "alert-summary"),
    ("Re-supply Qts Required", "re-supply-qts-required"),
    ("Lead Times", "lead-times"),
    ("Order Fill Rate", "order-fill-rate"),
    ("Emergency Orders", "emergency-orders"),
])

EPI_REPORT_LIST = OrderedDict([
    ("Reporting Rate", "reporting-rate"),
    ("Stock Status", "stock-status"),
    ("Consumption Profiles", "consumption-profiles"),
    ("Re-supply Qts Required", "re-supply-qts-required"),
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
}

USSD_PUSH_BACKEND = None

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
LOGISTICS_USE_STATIC_EMERGENCY_LEVELS = True
LOGISTICS_DEFAULT_PRODUCT_ACTIVATION_STATUS = True
LOGISTICS_REORDER_LEVEL_IN_MONTHS = 1
LOGISTICS_MAXIMUM_LEVEL_IN_MONTHS = 2
LOGISTICS_AGGRESSIVE_SOH_PARSING = False
LOGISTICS_EXCEL_EXPORT_ENABLED = False
LOGISTICS_LOGOUT_TEMPLATE = "logistics/loggedout.html"
LOGISTICS_USE_AUTO_CONSUMPTION = True
LOGISTICS_APPROVAL_REQUIRED = False
LOGISTICS_USERS_HAVE_ADMIN_ACCESS = True
LOGISTICS_DAYS_UNTIL_LATE_PRODUCT_REPORT = 2
LOGISTICS_REPORTING_CYCLE_IN_DAYS = 30
LOGISTICS_USE_BACKORDERS = False
LOGISTICS_IGNORE_DUPE_RECEIPTS_WITHIN = 60*60*24*2

LOGISTICS_CONSUMPTION = {
    "MINIMUM_TRANSACTIONS": 2,
    "MINIMUM_DAYS": 10,
    "LOOKBACK_DAYS": 60,            
    "INCLUDE_END_STOCKOUTS": True, 
}


SESSION_EXPIRE_AT_BROWSER_CLOSE=True

SITE_TITLE = "cStock"
BASE_TEMPLATE = "malawi/base.html"
BASE_TEMPLATE_SPLIT_2 = "logistics/base-split-2.html"

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


# data warehouse config
WAREHOUSE_RUNNER = 'logistics_project.apps.malawi.warehouse.runner.MalawiWarehouseRunner'
ENABLE_FACILITY_WORKFLOWS = False
LOGISTICS_USE_DEFAULT_HANDLERS = False
