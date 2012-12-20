"""
Test settings configuration for Jenkins CI.

Differences vs the base/production settings should be described as clearly as possible.

The localsettings.py for CI will only contain:

from logistics_project.deployments.ghana.settings_ci import *
"""

from logistics_project.deployments.ghana.settings_base import *

# Remove need for auditcare/couchlog to remove the need to run CouchDB on CI
if "auditcare" in APPS:
    APPS.remove("auditcare")
if "couchlog" in APPS:
    APPS.remove("couchlog")
if "auditcare.middleware.AuditMiddleware" in MIDDLEWARE_CLASSES:
    MIDDLEWARE_CLASSES.remove('auditcare.middleware.AuditMiddleware')

# Dummy cache will not work but local memory will for testing purposes
# and CI does not need to run Memcache
CACHES['default']['BACKEND']= 'django.core.cache.backends.locmem.LocMemCache'

# Generate xunit report
NOSE_ARGS = ('--with-xunit', )
