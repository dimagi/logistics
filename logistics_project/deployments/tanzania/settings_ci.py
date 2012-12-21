"""
Test settings configuration for Jenkins CI.

Differences vs the base/production settings should be described as clearly as possible.

The localsettings.py for CI will only contain:

from logistics_project.deployments.tanzania.settings_ci import *
"""

from logistics_project.deployments.tanzania.settings_base import *

# Use testing db config until Postgres auth on CI can be determined
DATABASES['default'] = TESTING_DATABASES['default']

# Remove need for auditcare/couchlog to remove the need to run CouchDB on CI
if "auditcare" in APPS:
    APPS.remove("auditcare")
if "auditcare" in PRIORITY_APPS:
    PRIORITY_APPS.remove("auditcare")
if "couchlog" in APPS:
    APPS.remove("couchlog")
if "gunicorn" in APPS:
    APPS.remove("gunicorn")
if "auditcare.middleware.AuditMiddleware" in MIDDLEWARE_CLASSES:
    MIDDLEWARE_CLASSES.remove('auditcare.middleware.AuditMiddleware')

# Dummy cache will not work but local memory will for testing purposes
# and CI does not need to run Memcache
CACHES['default']['BACKEND']= 'django.core.cache.backends.locmem.LocMemCache'

# Generate xunit report
NOSE_ARGS = ('--with-xunit', )

# Don't run the migrations to build the test DB
SOUTH_TESTS_MIGRATE = False
