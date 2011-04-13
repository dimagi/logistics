import os
import sys

filedir = os.path.dirname(__file__)

rootpath = os.path.join(filedir, "..", "logistics") 
sys.path.append(os.path.join(rootpath))
sys.path.append(os.path.join(rootpath,'..'))
sys.path.append(os.path.join(rootpath,'..','rapidsms'))
sys.path.append(os.path.join(rootpath,'..','rapidsms','lib'))
sys.path.append(os.path.join(rootpath,'..','rapidsms','lib','rapidsms'))
sys.path.append(os.path.join(rootpath,'..','rapidsms','lib','rapidsms','contrib'))
sys.path.append(os.path.join(rootpath,'..','submodules','django-cpserver'))
sys.path.append(os.path.join(rootpath,'..','submodules','dimagi-utils'))
sys.path.append(os.path.join(rootpath,'..','submodules','django-tablib'))
sys.path.append(os.path.join(rootpath,'..','submodules','tablib'))
sys.path.append(os.path.join(rootpath,'..','submodules','auditcare'))

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
