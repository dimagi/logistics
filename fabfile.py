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

"""
CONFIGURATION
"""

PATH_SEP = "/" # necessary to deploy from windows to *nix

env.code_cleanup = True
env.db_cleanup = True
env.db_name = "logistics"
env.remote = "origin"
env.branch = "master"
env.pathhack = False
env.stop_start = False

def do_nothing(): pass
env.extras = do_nothing

def _join(*args):
    if env.pathhack:
        return PATH_SEP.join(args)
    else:
        return os.path.join(*args)

def test():
    env.config = 'test'
    env.deploy_dir = os.path.dirname(__file__)
    env.code_dir = _join(list(env.deploy_dir, 'logistics'))
    env.hosts = ['localhost']

def malawi():
    """
    Malawi configuration
    """
    env.pathhack = True # sketchily, this must come before any join calls
    env.config = 'malawi'
    env.deploy_dir = '/home/sc4ccm/src'
    env.code_dir = _join(env.deploy_dir, 'logistics')
    env.code_cleanup = False
    env.db_cleanup = True
    env.db_name = "sc4ccm"
    env.stop_start = True
    env.branch = "malawi_model_support"
    env.hosts = ['sc4ccm@50.56.116.170']
    def malawi_extras():
        run("python manage.py malawi_init")
    env.extras = malawi_extras

def staging():
    env.config = 'staging'
    env.deploy_dir = '/home/ewsghana'
    env.code_dir = _join(env.deploy_dir, 'logistics')
    env.hosts = ['ewsghana@ewsghana.dyndns.org']

def production():
    env.config = 'production'
    env.deploy_dir = '/home/ewsghana'
    env.code_dir = _join(env.deploy_dir, 'logistics')
    env.hosts = ['ewsghana@ewsghana.dyndns.org']

"""
CAN'T TOUCH THIS
"""
def django_tests():
    """run django tests"""
    with cd('logistics'):
        local('./manage.py test --noinput', capture=False)

def update_requirements():
    """ update external dependencies """
    with cd(env.code_dir):
        run('ls')
        run('pip install --requirement %s' % _join(env.code_dir, "pip-requires.txt"))

def bootstrap():
    """ run this after you've checked out the code """
    with cd(env.code_dir):
        run('git submodule init')
        run('git submodule update')
        with cd('logistics'):
            run('./manage.py syncdb --noinput')
            run('./manage.py migrate --noinput')
            # this doesn't seem to exist
            #run('./bootstrap_db.py')
            env.extras()

def deploy():
    """ deploy code to some remote environment """
    require('config', provided_by=('test', 'staging', 'production', 'malawi'))
    if env.stop_start:
        sudo("/etc/init.d/apache2 stop")
        sudo("supervisorctl stop all")
    if env.config == 'production':
        if not console.confirm('Are you sure you want to deploy production?',
                               default=False):
            utils.abort('Production deployment aborted.')
    if env.code_cleanup:
        if not console.confirm('Are you sure you want to wipe out the "logistics" folder?',
                               default=False):
            utils.abort('Deployment aborted.')
        run('rm -rf logistics')
        run('git clone git://github.com/dimagi/logistics.git')
    else:
        with cd(env.code_dir):
            run('git checkout %(branch)s' % {"branch": env.branch})
            run('git pull %(repo)s %(branch)s' % {"repo": env.remote, "branch": env.branch})
    if env.db_cleanup:
        if not console.confirm('Are you sure you want to wipe out the database?',
                               default=False):
            utils.abort('Deployment aborted.')
        sudo('dropdb %(dbname)s' % {"dbname": env.db_name}, user="postgres")
        sudo('createdb %(dbname)s' % {"dbname": env.db_name}, user="postgres")
        
    bootstrap()
    if env.stop_start:
        sudo("/etc/init.d/apache2 start")
        sudo("supervisorctl start all")
    

def test_and_deploy():
    django_tests()
    deploy()

