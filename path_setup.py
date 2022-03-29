from __future__ import unicode_literals
import sys, os

def setup_path():
    filedir = os.path.dirname(__file__)
    sys.path.append(os.path.join(filedir, 'ex-submodules', 'rapidsms', 'lib'))
    sys.path.append(os.path.join(filedir, 'ex-submodules','django-scheduler'))
    sys.path.append(os.path.join(filedir, 'ex-submodules','rapidsms-alerts'))
    sys.path.append(os.path.join(filedir, 'ex-submodules','rapidsms-logistics'))
    sys.path.append(os.path.join(filedir, 'ex-submodules','rapidsms-groupmessaging'))
    sys.path.append(os.path.join(filedir, 'ex-submodules','django-datawarehouse'))
    sys.path.insert(0, os.path.join(filedir, 'ex-submodules','djtables','lib'))
