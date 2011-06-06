#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import sys, os
from django.core.management import execute_manager
import settings

filedir = os.path.dirname(__file__)
sys.path.append(os.path.join(filedir))
sys.path.append(os.path.join(filedir,'..'))
sys.path.append(os.path.join(filedir,'..','rapidsms'))
sys.path.append(os.path.join(filedir,'..','rapidsms','lib'))
sys.path.append(os.path.join(filedir,'..','rapidsms','lib','rapidsms'))
sys.path.append(os.path.join(filedir,'..','rapidsms','lib','rapidsms','contrib'))
sys.path.append(os.path.join(filedir,'..','submodules','django-cpserver'))
sys.path.append(os.path.join(filedir,'..','submodules','dimagi-utils'))
sys.path.append(os.path.join(filedir,'..','submodules','django-tablib'))
sys.path.append(os.path.join(filedir,'..','submodules','tablib'))
sys.path.append(os.path.join(filedir,'..','submodules','auditcare'))
sys.path.append(os.path.join(filedir,'..','submodules','couchlog'))

if __name__ == "__main__":
    execute_manager(settings)
