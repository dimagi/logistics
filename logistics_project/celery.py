from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

import os

from celery import Celery
from path_setup import setup_path

setup_path()

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'logistics_project.settings')

from django.conf import settings  # noqa

app = Celery('cstock')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
