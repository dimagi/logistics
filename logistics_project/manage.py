#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import sys, os


filedir = os.path.dirname(__file__)
sys.path.append(os.path.join(filedir))
sys.path.append(os.path.join(filedir,'..'))
sys.path.append(os.path.join(filedir,'..','ex-submodules', 'rapidsms', 'lib'))
sys.path.append(os.path.join(filedir,'..','ex-submodules','django-scheduler'))
sys.path.append(os.path.join(filedir,'..','ex-submodules','rapidsms-alerts'))
sys.path.append(os.path.join(filedir,'..','ex-submodules','rapidsms-logistics'))
sys.path.append(os.path.join(filedir,'..','ex-submodules','rapidsms-groupmessaging'))
sys.path.append(os.path.join(filedir,'..','ex-submodules','django-datawarehouse'))
sys.path.insert(0, os.path.join(filedir,'..','ex-submodules','djtables','lib'))


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "logistics_project.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
