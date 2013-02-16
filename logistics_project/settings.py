#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

# -------------------------------------------------------------------- #
#                          MAIN CONFIGURATION                          #
# -------------------------------------------------------------------- #

VERSION = '0.2.1' # This doesn't do anything yet, but what the hey.

# to help you get started quickly, many django/rapidsms apps are enabled
# by default. you may wish to remove some and/or add your own.
BASE_APPS = [

    # the essentials.
    "djtables",
    "rapidsms",
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
    "django.contrib.messages",
    "django.contrib.sessions",
    "django.contrib.contenttypes",
    
    "south",

    # nose must come after south because south has its own *test*
    "django_nose",
    
    # the rapidsms contrib apps.
    #"rapidsms.contrib.default",
    #"rapidsms.contrib.export",
    "rapidsms.contrib.httptester",
    "rapidsms.contrib.locations",
    "rapidsms.contrib.messagelog",
    "rapidsms.contrib.messaging",
    "alerts",
    "logistics_project.apps.registration",
    "logistics_project.apps.web_registration",
    "logistics",
    "logistics_project.apps.maps",
    "email_reports",
#    "logistics_project.apps.reports",
#    "logistics_project.apps.groupmessaging",
    #"django_cpserver", # pip install django-cpserver
    "registration",
    "groupmessaging",
    "taggit",
    "django_extensions",
    "warehouse"
]

PRIORITY_APPS = [] # if you want apps before the defaults
APPS = []          # if you want apps after the defaults

# -------------------------------------------------------------------- #
#                         BORING CONFIGURATION                         #
# -------------------------------------------------------------------- #


# debug mode is turned on as default, since rapidsms is under heavy
# development at the moment, and full stack traces are very useful
# when reporting bugs. don't forget to turn this off in production.
TEMPLATE_DEBUG = False


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
    # "django.contrib.auth.context_processors.auth", # TODO: django 1.2+ uses this
    "django.core.context_processors.auth", # deprecated
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.request",
    "rapidsms.context_processors.logo",
    "logistics.context_processors.custom_settings",
    "logistics.context_processors.google_analytics",
    "couchlog.context_processors.static_workaround"
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
        "PASSWORD": "",
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
CELERY_HEARTBEAT_FILE = '/tmp/logistics-heartbeat'

# kannel
KANNEL_URL = 'http://localhost:13000/status?password=CHANGEME'

DEFAULT_BACKEND = 'message_tester'
INTL_DIALLING_CODE = "+"
DOMESTIC_DIALLING_CODE = 0
STATIC_ROOT = "/static_root"
STATIC_URL = "/static"

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
COUCHDB_APPS=['auditcare','couchlog']
# This section should go at the BOTTOM of settings.py
# import local settings if we find them
#try to see if there's an environmental variable set for local_settings

LOGISTICS_LANDING_PAGE_VIEW = None
LOGISTICS_EXCEL_EXPORT_ENABLED = True
LOGISTICS_USE_STATIC_EMERGENCY_LEVELS = False
LOGISTICS_LOGIN_TEMPLATE = "logistics/login.html"
LOGISTICS_LOGOUT_TEMPLATE = "logistics/loggedout.html"
LOGISTICS_PASSWORD_CHANGE_TEMPLATE = "logistics/password_reset_form.html"
LOGISTICS_ALERT_GENERATORS = ['alerts.alerts.empty']
LOGISTICS_USE_AUTO_CONSUMPTION = False
LOGISTICS_DAYS_UNTIL_LATE_PRODUCT_REPORT = 7
LOGISTICS_DAYS_UNTIL_DATA_UNAVAILABLE = 21
LOGISTICS_APPROVAL_REQUIRED = False
LOGISTICS_USE_WAREHOUSE_TABLES = True

MAGIC_TOKEN = "changeme"

MAP_DEFAULT_LATITUDE  = -10.49
MAP_DEFAULT_LONGITUDE = 39.35

DEBUG=True

RAPIDSMS_HANDLERS_EXCLUDE_APPS = ["couchlog"]

# TODO: come back and clean this up
NO_LOGIN_REQUIRED_FOR = [
'password/reset',
'register',
'logout',
'activate',
'help',
'scmgr'
]

# AUDITCARE CONFIG
# users can fail login 10 times, resulting in a 1 hour cooloff period
AXES_LOGIN_FAILURE_LIMIT=100
AXES_LOGIN_FAILURE_LIMIT=1
AXES_LOCK_OUT_AT_FAILURE=False


COUCHLOG_BLUEPRINT_HOME = "%s%s" % (MEDIA_URL, "logistics/stylesheets/blueprint/")
COUCHLOG_DATATABLES_LOC = "%s%s" % (MEDIA_URL, "logistics/javascripts/jquery.dataTables.min.js")

SOUTH_MIGRATION_MODULES = {
    'rapidsms': 'logistics.migrations',
}

try:
    import sys
    if os.environ.has_key('LOCAL_SETTINGS'):
        # the LOCAL_SETTINGS environment variable is used by the build server
        sys.path.insert(0, os.path.dirname(os.environ['LOCAL_SETTINGS']))
        from settings_test import *
    else: 
        from localsettings import *
except ImportError as e:
    print e

INSTALLED_APPS = PRIORITY_APPS + BASE_APPS + APPS

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

# AUDITCARE CONFIG
# users can fail login 10 times, resulting in a 1 hour cooloff period
AXES_LOGIN_FAILURE_LIMIT=100
AXES_LOGIN_FAILURE_LIMIT=1
AXES_LOCK_OUT_AT_FAILURE=False
AUDITCARE_LOG_ERRORS = False


