#!/usr/bin/env python

import os
import sys

from path_setup import setup_path

setup_path()

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "logistics_project.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
