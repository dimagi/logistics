import os
import sys

filedir = os.path.dirname(__file__)

filedir = os.path.join(filedir, "..", "logistics_project")     
sys.path.append(os.path.join(filedir))
sys.path.append(os.path.join(filedir,'..'))
sys.path.append(os.path.join(filedir,'..','ex-submodules', 'rapidsms', 'lib'))
sys.path.append(os.path.join(filedir,'..','ex-submodules','django-scheduler'))
sys.path.append(os.path.join(filedir,'..','ex-submodules','rapidsms-alerts'))
sys.path.append(os.path.join(filedir,'..','ex-submodules','rapidsms-logistics'))
sys.path.append(os.path.join(filedir,'..','submodules','rapidsms-groupmessaging'))
sys.path.append(os.path.join(filedir,'..','ex-submodules','django-datawarehouse'))
sys.path.insert(0, os.path.join(filedir,'..','ex-submodules','djtables','lib'))

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
