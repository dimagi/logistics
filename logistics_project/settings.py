#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

# -------------------------------------------------------------------- #
#                          MAIN CONFIGURATION                          #
# -------------------------------------------------------------------- #


from __future__ import unicode_literals
SECRET_KEY = 'please change me in production'

# to help you get started quickly, many django/rapidsms apps are enabled
# by default. you may wish to remove some and/or add your own.
BASE_APPS = [

    # the essentials.
    "djtables",
    "rapidsms",
    # for email reports

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
    'django.contrib.staticfiles',
    "django.contrib.contenttypes",
    

    # the rapidsms contrib apps.
    "rapidsms.contrib.httptester",
    "rapidsms.contrib.locations",
    "rapidsms.contrib.messagelog",
    "rapidsms.contrib.messaging",
    "alerts",
    "logistics_project.apps.registration",
    "logistics",
    "groupmessaging",
    "taggit",
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


STATIC_ROOT = "static_root"
STATIC_URL = "/static/"
MEDIA_URL = "/media/"


# this is required for the django.contrib.sites tests to run, but also
# not included in global_settings.py, and is almost always ``1``.
# see: http://docs.djangoproject.com/en/dev/ref/contrib/sites/
SITE_ID = 1

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            # insert your TEMPLATE_DIRS here
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                "django.contrib.auth.context_processors.auth",
                'django.contrib.messages.context_processors.messages',
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.request",
                "rapidsms.context_processors.logo",
                "logistics.context_processors.custom_settings",
                "logistics.context_processors.user_profile",
            ],
        },
    },
]

# -------------------------------------------------------------------- #
#                           HERE BE DRAGONS!                           #
#        these settings are pure hackery, and will go away soon        #
# -------------------------------------------------------------------- #


# these apps should not be started by rapidsms in your tests, however,
# the mTEMPLATEodels and bootstrap will still be available through django.
TEST_EXCLUDED_APPS = [
    "django.contrib.sessions",
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "rapidsms",
    "rapidsms.contrib.ajax",
    "rapidsms.contrib.httptester",
]

# the project-level url patterns
ROOT_URLCONF = "logistics_project.urls"

# since we might hit the database from any thread during testing, the
# in-memory sqlite database isn't sufficient. it spawns a separate
# virtual database for each thread, and syncdb is only called for the
# first. this leads to confusing "no such table" errors. We create
# a named temporary instance instead.
import os
import tempfile
import sys

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "cstock",
        "USER": "root",
        "PASSWORD": "***",
        "HOST": "localhost",
    }
}

TESTING_DATABASES = {
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

# celery
CELERY_HEARTBEAT_FILE = '/tmp/logistics-heartbeat'
# Celery setup (using redis)
REDIS_URL = 'redis://localhost:6379/0'
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

# kannel
KANNEL_URL = 'http://localhost:13000/status?password=CHANGEME'

DEFAULT_BACKEND = 'message_tester'
INTL_DIALLING_CODE = "+"
DOMESTIC_DIALLING_CODE = 0

# reports
REPORT_URL = "/malawi/r"
EPI_REPORT_URL = "/malawi/f"

# This is a list of all district codes currently participating in EPI workflows.
# This list controls which districts are displayed in filters in reports as
# well as which districts are considered for country-level aggregation in the
# warehouse runner (which matters for some models, like reporting rates).
# To change which districts participate in EPI, just update this list.
EPI_DISTRICT_CODES = ['12', '13', '29', '30', '31', '37', '99']

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

# This section should go at the BOTTOM of settings.py
# import local settings if we find them
#try to see if there's an environmental variable set for local_settings

LOGISTICS_EXCEL_EXPORT_ENABLED = True
LOGISTICS_USE_STATIC_EMERGENCY_LEVELS = False
LOGISTICS_LOGOUT_TEMPLATE = "logistics/loggedout.html"
LOGISTICS_PASSWORD_CHANGE_TEMPLATE = "logistics/password_reset_form.html"
LOGISTICS_ALERT_GENERATORS = ['alerts.alerts.empty']
LOGISTICS_USE_AUTO_CONSUMPTION = False
LOGISTICS_DAYS_UNTIL_LATE_PRODUCT_REPORT = 7
LOGISTICS_DAYS_UNTIL_DATA_UNAVAILABLE = 21
LOGISTICS_APPROVAL_REQUIRED = False
MAGIC_TOKEN = "changeme"

MAP_DEFAULT_LATITUDE  = -10.49
MAP_DEFAULT_LONGITUDE = 39.35

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

DEBUG = False

NO_LOGIN_REQUIRED_FOR = [
    'malawi/is-kannel-up',
    'accounts/logout',
]

if os.environ.get('GITHUB_TESTS', False):
    from .testsettings import *

try:
    import sys
    from .localsettings import *
except ImportError:
    pass

INSTALLED_APPS = PRIORITY_APPS + BASE_APPS + APPS
