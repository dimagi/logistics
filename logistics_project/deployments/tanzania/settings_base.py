# you should configure your database here before doing any real work.
# see: http://docs.djangoproject.com/en/dev/ref/settings/#databases
import os
LOGISTICS_CONFIG = 'logistics_project.apps.tanzania.config'

PRIORITY_APPS = [ "logistics_project.apps.migration" ]
    
                 
APPS = [
    "django.contrib.webdesign",
    "logistics_project.apps.tanzania",
    "scheduler",
    "taggit",
]

RAPIDSMS_TABS = [
    ("logistics_project.apps.tanzania.views.dashboard",       "Dashboard"),
#    ("logistics_project.apps.tanzania.reportcalcs.new_reports",       "Dashboard"),
#    ("logistics_project.apps.tanzania.views.facilities_index",       "Current Stock Status"),
#    ("logistics_project.apps.tanzania.views.facilities_ordering",       "Ordering Status"),
#    ("logistics_project.apps.tanzania.views.supervision",       "Supervision"),
    ("logistics_project.apps.tanzania.reportcalcs.new_reports",       "Reports"),
    ("logistics_project.apps.maps.views.dashboard",       "Maps"),

#    ("logistics.views.dashboard",       "Facilities"),
#    ("logistics_project.apps.malawi.views.help",       "Help"),
#    ("logistics_project.apps.malawi.views.contacts",       "Management", "is_superuser"),
#    ("logistics_project.apps.malawi.views.monitoring",       "M & E", "is_superuser"),
    ("registration",                          "Registration", "is_superuser"),
    ("rapidsms.contrib.messagelog.views.message_log",       "Log", "is_superuser"),
    ("rapidsms.contrib.httptester.views.generate_identity", "Tester", "is_superuser"),
    ("tz_sms_schedule",       "Help"),

]

INSTALLED_BACKENDS = {
    # tester
    "message_tester": {
        "ENGINE": "rapidsms.backends.bucket",
    },
    # message migration
    "migration": {
        "ENGINE": "logistics_project.apps.migration.backends.migration",
    },
    # push
    "push": {
        "ENGINE": "logistics_project.backends.push",
        'host': 'localhost', 'port': '8081', # used for spawned backend WSGI server
        'config': {
            'url': "https://dragon.operatelecom.com:1089/Gateway",
            'channel': "24358",
            'service': "147118",
            'password': 'CHANGEME',
        }
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

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'logistics_project.apps.ewsghana.middleware.RequireLoginMiddleware',
    'django.middleware.locale.LocaleMiddleware', 
)

# 1.3
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}

# 1.2
CACHE_BACKEND = 'memcached://127.0.0.1:11211/'

TEMPLATE_CONTEXT_PROCESSORS = [
    "django.core.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.request",
    "rapidsms.context_processors.logo",
    "logistics.context_processors.custom_settings",
    "logistics.context_processors.stock_cutoffs",
    "logistics.context_processors.google_analytics",
    "logistics.context_processors.global_nav_mode",
    "logistics_project.apps.tanzania.context_processors.language_in_request",
    "logistics_project.apps.tanzania.context_processors.location_scope_hide_show",
    "couchlog.context_processors.static_workaround"
]

DJANGO_LOG_FILE = "logistics.django.log"
LOG_SIZE = 1000000
LOG_LEVEL   = "DEBUG"
LOG_FILE    = "logistics.log"
LOG_FORMAT  = "[%(name)s]: %(message)s"
LOG_BACKUPS = 256 # number of logs to keep

DEFAULT_RESPONSE = "Sorry, I could not understand your message. Please contact your supervisor for help."
COUNTRY = "MOHSW-MOHSW"
TIME_ZONE="Africa/Maputo"
COUNTRY_DIALLING_CODE = 265

LANGUAGES = (
  ('sw', 'Swahili'),
  ('en', 'English'),
)

LANGUAGE_CODE = "sw"
 
NO_LOGIN_REQUIRED_FOR = ['password/reset',
                         'register',
                         'logout',
                         'activate',
                         'help',
                         'scmgr',
                         'reports/pdf']

# change to not make product reports "active" by default
# should be True for Malawi, False for Ghana
LOGISTICS_LANDING_PAGE_VIEW = "tz_dashboard"
LOGISTICS_USE_STATIC_EMERGENCY_LEVELS = True
LOGISTICS_DEFAULT_PRODUCT_ACTIVATION_STATUS = True
LOGISTICS_REORDER_LEVEL_IN_MONTHS = 3
LOGISTICS_MAXIMUM_LEVEL_IN_MONTHS = 7
LOGISTICS_AGGRESSIVE_SOH_PARSING = False
LOGISTICS_GHANA_HACK_CREATE_SCHEDULES = False
LOGISTICS_EXCEL_EXPORT_ENABLED = False
LOGISTICS_LOGIN_TEMPLATE = "logistics/login.html"
LOGISTICS_LOGOUT_TEMPLATE = "logistics/loggedout.html"
LOGISTICS_USE_AUTO_CONSUMPTION = True
LOGISTICS_APPROVAL_REQUIRED = True
LOGISTICS_USE_COMMODITY_EQUIVALENTS = False
LOGISTICS_PRODUCT_ALIASES = {'iucd': 'id' ,
                             'depo': 'dp',
                             'impl': 'ip',
                             'coc': 'cc',
                             'pop': 'pp'}
LOGISTICS_USE_DEFAULT_HANDLERS = False
LOGISTICS_URL_GENERATOR_FUNCTION = "logistics_project.apps.tanzania.views.tz_location_url"
LOGISTICS_MAP_POPUP_FUNCTION = "logistics_project.apps.tanzania.templatetags.tz_tags.get_map_popup"
LOGISTICS_USE_LOCATION_SESSIONS = True
LOGISTICS_NAVIGATION_MODE = "param" 
LOGISTICS_USE_SPOT_CACHING = True
LOGISTICS_SPOT_CACHE_TIMEOUT = 60 * 60

LOGO_LEFT_URL="/static/tanzania/img/Tanzania-Flag.png"
LOGO_RIGHT_URL="/static/tanzania/img/TZ-Ministry-logo.gif"
SITE_TITLE="ILSGateway"
BASE_TEMPLATE="tanzania/base.html"
BASE_TEMPLATE_SPLIT_2="logistics/base-split-2.html"

LOGISTICS_ALERT_GENERATORS = [
    "logistics_project.apps.tanzania.alerts.randr_not_submitted",
    "logistics_project.apps.tanzania.alerts.randr_not_responded",
    "logistics_project.apps.tanzania.alerts.delivery_not_received",
    "logistics_project.apps.tanzania.alerts.delivery_not_responding",
    "logistics_project.apps.tanzania.alerts.soh_not_responding",
    "logistics_project.apps.tanzania.alerts.product_stockout",
    "logistics_project.apps.tanzania.alerts.no_primary_contact",
]

STATIC_LOCATIONS = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))), "static", "tanzania", "migration", "all_facilities.csv")

REPORT_FOLDER = "tanzania/reports"
