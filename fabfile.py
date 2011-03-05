#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

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
    env.deploy_dir = os.path.dirname(__file__)
    env.code_dir = os.path.join(env.deploy_dir, 'logistics')
    env.hosts = ['rowena@localhost']

def staging():
    env.config = 'staging'
    env.deploy_dir = '/home/ewsghana'
    env.code_dir = os.path.join(env.deploy_dir, 'logistics')
    env.hosts = ['ewsghana@ewsghana.dyndns.org']

def production():
    env.config = 'production'
    env.deploy_dir = '/home/ewsghana'
    env.code_dir = os.path.join(env.deploy_dir, 'logistics')
    env.hosts = ['ewsghana@ewsghana.dyndns.org']

"""""""""""""""""
CAN'T TOUCH THIS
"""""""""""""""""
def django_tests():
    """run django tests"""
    with cd('logistics'):
        local('./manage.py test --noinput', capture=False)

def update_requirements():
    """ update external dependencies """
    with cd(env.code_dir):
        run('ls')
        run('pip install --requirement %s' % os.path.join(env.code_dir, "pip-requires.txt"))

def bootstrap():
    """ run this after you've checked out the code """
    with cd(env.code_dir):
        run('git submodule init')
        run('git submodule update')
        with cd('logistics'):
            run('./manage.py syncdb --noinput')
            run('./bootstrap_db.py')

def deploy():
    """ deploy code to some remote environment """
    require('config', provided_by=('test', 'staging', 'production'))
    if env.config == 'production':
        if not console.confirm('Are you sure you want to deploy production?',
                               default=False):
            utils.abort('Production deployment aborted.')
    if not console.confirm('Are you sure you want to wipe out the "logistics" folder?',
                           default=False):
        utils.abort('Deployment aborted.')
    run('rm -rf logistics')
    run('git clone git://github.com/dimagi/logistics.git')
    bootstrap()

def test_and_deploy():
    django_tests()
    deploy()

