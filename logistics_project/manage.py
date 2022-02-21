#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import sys, os
from django.core.management import execute_manager

filedir = os.path.dirname(__file__)
sys.path.append(os.path.join(filedir))
sys.path.append(os.path.join(filedir,'..'))
sys.path.append(os.path.join(filedir,'..','rapidsms','lib'))
sys.path.append(os.path.join(filedir,'..','submodules','django-cpserver'))
sys.path.append(os.path.join(filedir,'..','submodules','dimagi-utils'))
sys.path.append(os.path.join(filedir,'..','submodules','django-tablib'))
sys.path.append(os.path.join(filedir,'..','submodules','tablib'))
sys.path.append(os.path.join(filedir,'..','submodules','django-scheduler'))
sys.path.append(os.path.join(filedir,'..','submodules','rapidsms-alerts'))
sys.path.append(os.path.join(filedir,'..','submodules','email-reports'))
sys.path.append(os.path.join(filedir,'..','submodules','rapidsms-dupe-checker'))
sys.path.append(os.path.join(filedir,'..','ex-submodules','rapidsms-logistics'))
sys.path.append(os.path.join(filedir,'..','submodules','rapidsms-groupmessaging'))
sys.path.append(os.path.join(filedir,'..','submodules','django-datawarehouse'))

sys.path.insert(0, os.path.join(filedir,'..','submodules','dimagi-djtables','lib'))

if __name__ == "__main__":
    import settings
    execute_manager(settings)
