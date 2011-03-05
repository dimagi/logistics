from __future__ import with_statement
import os
import sys
import uuid
from datetime import datetime

from fabric import utils
from fabric.api import *
from fabric.contrib import files, console
from fabric.decorators import hosts

"""""""""""""""    
CONFIGURATION
"""""""""""""""
def test():
    env.config = 'test'
    env.fab_user = 'rowena'
    env.hosts = ['localhost']

def staging():
    env.config = 'staging'
    env.fab_user = 'ewsghana'
    env.hosts = ['ewsghana.dyndns.org']

def production():
    env.config = 'production'
    env.fab_user = 'ewsghana'
    env.hosts = ['ewsghana.dyndns.org']

"""""""""""""""""
CAN'T TOUCH THIS
"""""""""""""""""
def _setup_paths():
    env.cwd = os.path.dirname(__file__)
    env.code_root = os.path.join(env.cwd, 'logistics')

def django_tests():
    """Run django tests"""
    with cd('logistics'):
        local('./manage.py test', capture=False)

def update_requirements():
    """ update external dependencies on remote host """
    _setup_paths()
    local('pip install --requirement %s' % os.path.join(env.cwd, "pip-requires.txt"))

def bootstrap():
    """ Run this after you've checked out the code """
    update_requirements()
    run('git submodule init', capture=False)
    run('git submodule update', capture=False)
    with cd('logistics'):
        run('./manage.py syncdb', capture=False)
        run('./setup.py', capture=False)

def deploy():
    require('fab_user', provided_by=('test', 'staging', 'production'))
    if env.config == 'production':
        if not console.confirm('Are you sure you want to deploy production?',
                               default=False):
            utils.abort('Production deployment aborted.')
    run('git clone git://github.com/dimagi/logistics.git', capture=False)
    with cd('logistics'):
        bootstrap()

def test_and_deploy():
    django_tests()
    deploy()

