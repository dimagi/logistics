"""
Test settings configuration for Jenkins CI.

Differences vs the base/production settings should be described as clearly as possible.

The localsettings.py for CI will only contain:

from logistics_project.deployments.malawi.settings_ci import *
"""
from __future__ import unicode_literals

from logistics_project.deployments.malawi.settings_base import *

# Use testing db config until Postgres auth on CI can be determined
DATABASES['default'] = TESTING_DATABASES['default']


# Dummy cache will not work but local memory will for testing purposes
# and CI does not need to run Memcache
CACHES['default']['BACKEND']= 'django.core.cache.backends.locmem.LocMemCache'

# Generate xunit report
NOSE_ARGS = ('--with-xunit', )
