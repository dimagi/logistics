#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

# -------------------------------------------------------------------- #
#                          MAIN CONFIGURATION                          #
# -------------------------------------------------------------------- #

VERSION = '0.2.1' # This doesn't do anything yet, but what the hey.

# to help you get started quickly, many django/rapidsms apps are enabled
# by default. you may wish to remove some and/or add your own.
INSTALLED_APPS = [

    # the essentials.
    "django_nose",
    "djtables",
    "rapidsms",
    "django_extensions",
    # for email reports
    "djcelery", # pip install django-celery
    "djkombu", # pip install django-kombu

    # common dependencies (which don't clutter up the ui).
    "rapidsms.contrib.handlers",
    "rapidsms.contrib.ajax",

    # enable the django admin using a little shim app (which includes
    # the required urlpatterns), and a bunch of undocumented apps that
    # the AdminSite seems to explode without.
    "django.contrib.sites",
    "django.contrib.auth",
    "django.contrib.admin",
    "django.contrib.sessions",
    "django.contrib.contenttypes",
    
    "south",
    
    # the rapidsms contrib apps.
    #"rapidsms.contrib.default",
    "rapidsms.contrib.export",
    "rapidsms.contrib.httptester",
    "rapidsms.contrib.locations",
    "rapidsms.contrib.messagelog",
    "rapidsms.contrib.messaging",
    "rapidsms.contrib.scheduler",
    "rapidsms.contrib.echo",
    #"rapidsms.contrib.stringcleaning",
    #"rapidsms.contrib.registration",
    "logistics.apps.malawi",
    "logistics.apps.registration",
    "logistics.apps.web_registration",
    "logistics.apps.logistics",
    "logistics.apps.ewsghana",
    "logistics.apps.reports",
    "logistics.apps.smsgh",
    #"django_cpserver", # pip install django-cpserver
    "auditcare",
    "registration",
]

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'auditcare.middleware.AuditMiddleware',
    #'logistics.apps.ewsghana.middleware.RequireLoginMiddleware',
)


# this rapidsms-specific setting defines which views are linked by the
# tabbed navigation. when adding an app to INSTALLED_APPS, you may wish
# to add it here, also, to expose it in the rapidsms ui.
RAPIDSMS_TABS = [
    ("logistics_dashboard",                    "Stock Levels"),
    ("reporting",                              "Reporting Rates"),
    #("input_stock",                          "Input Stock"),
    ("registration",                          "Registration"),
    ("rapidsms.contrib.messagelog.views.message_log",       "Message Log"),
    #("rapidsms.contrib.messaging.views.messaging",          "Messaging"),
    #("rapidsms.contrib.locations.views.locations",          "Map"),
    ("rapidsms.contrib.scheduler.views.index",              "Event Scheduler"),
    #("ewsghana_reporting",  				    "Usage"),
    #("input_stock",      				    "Input Stock"),
    #("ewsghana_scheduled_reports", 	                    "Configuration"),
    #("email_reports",      			            "Email Reports"),
    ("help",      			                    "Help"),
    #("rapidsms.contrib.messaging.views.messaging",         "Messaging"),
    #("rapidsms.contrib.locations.views.locations",         "Map"),
    #("rapidsms.contrib.scheduler.views.index",              "Event Scheduler"),
    ("rapidsms.contrib.httptester.views.generate_identity", "Message Tester"),
]

# TODO: move this configuration over to urls.py
SMS_REGISTRATION_VIEW='ewsghana_sms_registration'
SMS_REGISTRATION_EDIT='ewsghana_registration_edit'

# -------------------------------------------------------------------- #
#                         BORING CONFIGURATION                         #
# -------------------------------------------------------------------- #


# debug mode is turned on as default, since rapidsms is under heavy
# development at the moment, and full stack traces are very useful
# when reporting bugs. don't forget to turn this off in production.
TEMPLATE_DEBUG = True


# after login (which is handled by django.contrib.auth), redirect to the
# dashboard rather than 'accounts/profile' (the default).
LOGIN_REDIRECT_URL = "/"


# use django-nose to run tests. rapidsms contains lots of packages and
# modules which django does not find automatically, and importing them
# all manually is tiresome and error-prone.
TEST_RUNNER = "django_nose.NoseTestSuiteRunner"


# for some reason this setting is blank in django's global_settings.py,
# but it is needed for static assets to be linkable.
MEDIA_URL = "/static/"


# this is required for the django.contrib.sites tests to run, but also
# not included in global_settings.py, and is almost always ``1``.
# see: http://docs.djangoproject.com/en/dev/ref/contrib/sites/
SITE_ID = 1


# these weird dependencies should be handled by their respective apps,
# but they're not, so here they are. most of them are for django admin.
TEMPLATE_CONTEXT_PROCESSORS = [
    "django.core.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.request",
    "rapidsms.context_processors.logo",
]


# -------------------------------------------------------------------- #
#                           HERE BE DRAGONS!                           #
#        these settings are pure hackery, and will go away soon        #
# -------------------------------------------------------------------- #


# these apps should not be started by rapidsms in your tests, however,
# the models and bootstrap will still be available through django.
TEST_EXCLUDED_APPS = [
    "django.contrib.sessions",
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "rapidsms",
    "rapidsms.contrib.ajax",
    "rapidsms.contrib.httptester",
    "djcelery"
]

# the project-level url patterns
ROOT_URLCONF = "urls"

# since we might hit the database from any thread during testing, the
# in-memory sqlite database isn't sufficient. it spawns a separate
# virtual database for each thread, and syncdb is only called for the
# first. this leads to confusing "no such table" errors. We create
# a named temporary instance instead.
import os
import tempfile
import sys

# for postgresql:
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "logistics",
        "USER": "postgres",
        "PASSWORD": "dimagi4vm",
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

AUTH_PROFILE_MODULE = "logistics.LogisticsProfile"

# celery
CARROT_BACKEND = "django"

DEFAULT_BACKEND = 'smsgh'
DEFAULT_RESPONSE = "Sorry, I could not understand your message. Please contact your DHIO for help, or visit http://www.ewsghana.com"
INTL_DIALLING_CODE = "+"
COUNTRY_DIALLING_CODE = 233
DOMESTIC_DIALLING_CODE = 0
COUNTRY = "malawi"
STATIC_ROOT = "/static_root"
STATIC_URL = "/static"
TIME_ZONE="Africa/Accra"
filedir = os.path.dirname(__file__)

STATIC_LOCATIONS = os.path.join(os.path.dirname(os.path.abspath(os.path.dirname(__file__))), "static", "malawi", "health_centers.csv")
# email settings used for sending out email reports
EMAIL_LOGIN="name@dimagi.com"
EMAIL_PASSWORD="changeme"
EMAIL_SMTP_HOST="smtp.gmail.com"
EMAIL_SMTP_PORT=587
ACCOUNT_ACTIVATION_DAYS=30

EMAIL_HOST='smtp.gmail.com'
EMAIL_HOST_PASSWORD='changeme'
EMAIL_HOST_USER='name@dimagi.com'
EMAIL_PORT=587
EMAIL_USE_TLS=True

COUCH_SERVER_ROOT='127.0.0.1:5984'
COUCH_USERNAME=''
COUCH_PASSWORD=''
COUCH_DATABASE_NAME='logistics'
COUCHDB_APPS=['auditcare',]

# change to not make product reports "active" by default
# should be True for Malawi, False for Ghana
LOGISTICS_DEFAULT_PRODUCT_ACTIVATION_STATUS = True
LOGISTICS_REORDER_LEVEL_IN_MONTHS = 1
LOGISTICS_MAXIMUM_LEVEL_IN_MONTHS = 2


# This section should go at the BOTTOM of settings.py
# import local settings if we find them
try:
    from localsettings import *
except ImportError:
    pass
if ('test' in sys.argv) and ('sqlite' not in DATABASES['default']['ENGINE']):
    DATABASES = TESTING_DATABASES
    for db_name in DATABASES:
        DATABASES[db_name]['TEST_NAME'] = os.path.join(
            tempfile.gettempdir(),
            "%s.rapidsms.test.sqlite3" % db_name)


def get_server_url(server_root, username, password):
    if username and password:
        return "http://%(user)s:%(pass)s@%(server)s" % \
            {"user": username,
             "pass": password, "server": server_root } 
    else:
        return "http://%(server)s" % {"server": server_root }
COUCH_SERVER = get_server_url(COUCH_SERVER_ROOT, COUCH_USERNAME, COUCH_PASSWORD)
COUCH_DATABASE = "%(server)s/%(database)s" % {"server": COUCH_SERVER, "database": COUCH_DATABASE_NAME }

COUCHDB_DATABASES = [(app_label, COUCH_DATABASE) for app_label in COUCHDB_APPS]

DEBUG=True

# TODO: come back and clean this up
NO_LOGIN_REQUIRED_FOR = [
'password/reset',
'register',
'logout',
'activate',
]

# AUDITCARE CONFIG
# users can fail login 10 times, resulting in a 1 hour cooloff period
AXES_LOGIN_FAILURE_LIMIT=10
AXES_LOGIN_FAILURE_LIMIT=1

LOGO_LEFT_URL="/static/malawi/images/malawi-flag.jpg"
LOGO_RIGHT_URL="/static/ewsghana/images/jsi_logo.png"
SITE_TITLE="cStock"
BASE_TEMPLATE="malawi/base.html"
BASE_TEMPLATE_SPLIT_2="ewsghana/base-split-2.html"
