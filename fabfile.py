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
env.virtualenv_root = None

def do_nothing(): pass
env.extras = do_nothing

def enter_virtualenv():
    """
    modify path to use virtualenv's python

    usage:

        with enter_virtualenv():
            run('python script.py')

    """
    if env.virtualenv_root:
        return prefix('PATH=%(virtualenv_root)s/bin/:PATH' % env)
    else:
        # this is just a noop
        return prefix("pwd")

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

def _malawi_shared():
    env.pathhack = True # sketchily, this must come before any join calls
    env.config = 'malawi'
    env.code_dir = _join(env.deploy_dir, 'logistics')
    env.code_cleanup = False
    env.db_cleanup = False
    env.stop_start = True
    env.branch = "malawi-dev"
    def malawi_extras():
        run("python manage.py malawi_init")
        run("python manage.py loaddata ../deploy/malawi/initial_data.json")
        sudo("/etc/init.d/memcached restart")
    env.extras = malawi_extras

def malawi():
    """
    Malawi configuration (vmracks)
    """
    env.deploy_dir = '/home/dimagi/src'
    env.db_name = "cstock"
    env.hosts = ['dimagi@216.240.181.53']
    _malawi_shared()
    
def malawi_old():
    """
    Malawi configuration (rackspace)
    """
    env.deploy_dir = '/home/sc4ccm/src'
    env.db_name = "sc4ccm"
    env.hosts = ['sc4ccm@50.56.116.170']
    _malawi_shared()

def _tz_shared():
    env.pathhack = True # sketchily, this must come before any join calls
    env.config = 'tz'
    env.code_dir = _join(env.deploy_dir, 'logistics')
    env.code_cleanup = False
    env.db_cleanup = False
    env.stop_start = True
    env.branch = "tz-dev"
    def tz_extras():
        sudo("/etc/init.d/memcached restart")
    env.extras = tz_extras

def tz_staging():
    """
    TZ configuration (staging)
    """
    env.deploy_dir = '/home/dimagivm/src'
    env.db_name = "logistics"
    env.hosts = ['dimagivm@ilsstaging.dimagi.com']
    _tz_shared()


def tz_production():
    """
    TZ configuration (staging)
    """
    env.deploy_dir = '/home/dimagi/src'
    env.db_name = "logistics"
    env.hosts = ['dimagi@ilsgateway.com']
    _tz_shared()
    env.virtualenv_root = "/home/dimagi/src/logistics-env"


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
        with enter_virtualenv():
            run('pip install -r %s' % _join(env.code_dir, "pip-requires.txt"))

def bootstrap(subdir='logistics'):
    """ run this after you've checked out the code """
    with cd(env.code_dir):
        run('git submodule init')
        run('git submodule update')
        update_requirements()
        with cd(subdir):
            with enter_virtualenv():
                run('./manage.py syncdb --noinput')
                run('./manage.py migrate --noinput')
                # this doesn't seem to exist
                #run('./bootstrap_db.py')
                env.extras()

def deploy():
    """ deploy code to some remote environment """
    require('config', provided_by=('test', 'staging', 'production', 'malawi'))
    if env.stop_start:
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
        
    bootstrap(subdir='logistics_project' if env.config.startswith('tz') else 'logistics')
    if env.stop_start:
        sudo("/etc/init.d/apache2 reload")
        sudo("supervisorctl start all")
    

def test_and_deploy():
    django_tests()
    deploy()

