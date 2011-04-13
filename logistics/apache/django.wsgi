import os
import sys

filedir  = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
sys.path.append(os.path.join(filedir))
sys.path.append(os.path.join(filedir,'..'))
sys.path.append(os.path.join(filedir,'..','rapidsms'))
sys.path.append(os.path.join(filedir,'..','rapidsms','lib'))
sys.path.append(os.path.join(filedir,'..','rapidsms','lib','rapidsms'))
sys.path.append(os.path.join(filedir,'..','rapidsms','lib','rapidsms','contrib'))
sys.path.append(os.path.join(filedir,'..','submodules','django-cpserver'))

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

