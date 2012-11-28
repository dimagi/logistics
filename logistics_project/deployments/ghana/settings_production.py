# you should configure your database here before doing any real work.
# see: http://docs.djangoproject.com/en/dev/ref/settings/#databases

ADMINS = (('Rowena','ews-dev@dimagi.com'), )
MANAGERS = (('Rowena','ews-dev@dimagi.com'), )
SEND_BROKEN_LINK_EMAILS = True

CACHE_BACKEND = 'memcached://127.0.0.1:11211/'

APPS = [
    "auditcare",
    "rapidsms.contrib.scheduler",
    "logistics_project.apps.ewsghana",
    "logistics_project.apps.smsgh",
    "cpserver",
]

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'auditcare.middleware.AuditMiddleware',
    'logistics_project.apps.ewsghana.middleware.AutoLogout',
    'logistics_project.apps.ewsghana.middleware.RequireLoginMiddleware',
    'logistics.middleware.CachedTemplateMiddleware',
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
    #("rapidsms.contrib.httptester.views.generate_identity", "Message Tester"),
    ("maps_dashboard",                                      "Maps"),
]

# for postgresql:
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "logistics",
        "USER": "postgres",
        "PASSWORD": "password",
        "HOST": "localhost",
    }
}

TESTING_DATABASES= {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",#
        "NAME": "logistics.sqlite3",
    }
}

DJANGO_LOG_FILE = "/opt/logistics_projects/log/logistics.django.log"
LOG_SIZE = 1000000
LOG_LEVEL   = "ERROR"
LOG_FILE    = "/opt/logistics_project/log/router.logistics.log"
LOG_FORMAT  = "[%(name)s]: %(message)s"
LOG_BACKUPS = 256 # number of logs to keep

DEFAULT_RESPONSE = "Sorry, I could not understand your message. Please contact your DHIO for help, or visit http://www.ewsghana.com"
COUNTRY = "ghana"
TIME_ZONE="Africa/Accra"
COUNTRY_DIALLING_CODE = 233

INSTALLED_BACKENDS = {
    #"att": {
    #    "ENGINE": "rapidsms.backends.gsm",
    #    "PORT": "/dev/ttyUSB0"
    #},
    #"verizon": {
    #    "ENGINE": "rapidsms.backends.gsm,
    #    "PORT": "/dev/ttyUSB1"
    #},
    "smsgh": {
        "ENGINE": "logistics_project.backends.smsgh_http",
        "PORT": 8002,
        "HOST": "50.56.82.64",
        "gateway_url" : "http://api.smsgh.com/v2/messages/send",
        "params_outgoing": "username=username&password=password&from=%(from)s&to=%(phone_number)s&text=%(message)s",
        "params_incoming": "snr=%(phone_number)s&msg=%(message)s"
    },
    #"end2end": {
    #    "ENGINE": "rapidsms.backends.http",
    #    "PORT": 8002,
    #    "gateway_url" : "http://gw1.promessaging.com/sms.php",
    #    "params_outgoing": "user=my_username&password=my_password&id=%(phone_number)s&text=%(message)s",
    #    "params_incoming": "snr=%(phone_number)s&msg=%(message)s"
    #},
    "message_tester": {
        "ENGINE": "rapidsms.backends.bucket",
    },
}

DEFAULT_BACKEND = 'smsgh'
STATIC_ROOT="/opt/logistics_project/src/logistics/logistics_project/static"

# email settings used for sending out email reports
EMAIL_LOGIN="sender@gmail.com"
EMAIL_PASSWORD="password"
EMAIL_SMTP_HOST="smtp.gmail.com"
EMAIL_SMTP_PORT=587
ACCOUNT_ACTIVATION_DAYS=30

EMAIL_HOST='smtp.gmail.com'
EMAIL_HOST_PASSWORD='password'
EMAIL_HOST_USER='sender@gmail.com'
EMAIL_PORT=587
EMAIL_USE_TLS=True

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

AUDITCARE_LOG_ERRORS = False

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

DEBUG=False
TEMPLATE_DEBUG=False

LOGISTICS_ALERT_GENERATORS = [
    'logistics.alerts.non_reporting_facilities',
    'logistics.alerts.facilities_without_reporters',
    'logistics_project.apps.ewsghana.alerts.facilities_without_incharge',
    'logistics.alerts.facilities_without_reminders',
    'logistics_project.apps.ewsghana.alerts.contact_without_phone',
]

GOOGLE_ANALYTICS_ID = "123"

SOUTH_MIGRATION_MODULES = {
    'rapidsms': 'deployments.ghana.migrations.rapidsms',
    'logistics': 'deployments.ghana.migrations.logistics',
    'ewsghana': 'deployments.ghana.migrations.ewsghana',
    'email_reports': 'deployments.ghana.migrations.email_reports',
    'locations': 'deployments.ghana.migrations.locations',
}

AUTO_LOGOUT_DELAY = 300
