from logistics_project.deployments.malawi.settings_base import *


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": 'cstock',
        "USER": os.environ.get('DB_USER'),
        "PASSWORD": os.environ.get('DB_PASSWORD'),
        "HOST": "localhost",
        "PORT": "3306",
    }
}
