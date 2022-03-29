from __future__ import print_function
from __future__ import unicode_literals
from logistics_project.deployments.malawi.settings_base import *

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": 'cstock',
        "USER": os.environ.get('DB_USER'),
        "PASSWORD": os.environ.get('DB_PASSWORD'),
        "HOST": "127.0.0.1",
        "PORT": "3306",
    }
}
