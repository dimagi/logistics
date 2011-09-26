import os
import sys


project_root = '/home/dimagivm/projects/ilsgateway-app-dev'

for dir in ["lib", "apps"]:
        path = os.path.join(project_root, dir)
        sys.path.insert(0, path)

sys.path.insert(0, project_root)
sys.path.append('/home/dimagivm/projects')

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import settings
from logconfig import init_file_logging
init_file_logging(settings.LOG_FILE, settings.LOG_SIZE,
                  settings.LOG_BACKUPS, settings.LOG_LEVEL,
                  settings.LOG_FORMAT)

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
