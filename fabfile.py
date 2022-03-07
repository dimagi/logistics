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
from subprocess import Popen

"""
CONFIGURATION
"""

PATH_SEP = "/" # necessary to deploy from windows to *nix

env.code_cleanup = True
env.db_cleanup = True
env.db_name = "logistics"
env.db_user = "root"
env.local_db_user = "root"
env.db_type = "mysql"
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


def malawi():
    """
    Malawi configuration (vmracks)
    """
    env.deploy_dir = '/home/dimagi/src'
    env.db_name = "cstock"
    env.hosts = ['dimagi@10.84.168.89']
    _malawi_shared()
    
def malawi_old():
    """
    Malawi configuration (rackspace)
    """
    env.deploy_dir = '/home/sc4ccm/src'
    env.db_name = "sc4ccm"
    env.hosts = ['sc4ccm@50.56.116.170']
    _malawi_shared()


def production():
    malawi()


def _local_sudo(command, user=None):
    if user:
        return Popen("sudo %s" % command, shell=True)
    else:
        return Popen("sudo -u %s %s" % (user, command), shell=True)

def _get_db(dumpname):
    sudo("gzip /tmp/%s" % dumpname)
    get("/tmp/%s.gz" % dumpname, local_path="/tmp/%s.gz" % dumpname)
    local("gunzip /tmp/%s.gz" % dumpname)


def sync_postgres_db():
    """ Untested as of yet. """
    dumpname = "db_%s_%s.sql" % (env.db_name, datetime.now().isoformat())
    sudo("pg_dump %(dbname)s > /tmp/%(dumpname)s" % {"dbname": env.db_name, "dumpname": dumpname}, user="postgres")
    _get_db(dumpname)
    _local_sudo('dropdb %(dbname)s' % {"dbname": env.db_name}, user="postgres")
    _local_sudo('createdb %(dbname)s' % {"dbname": env.db_name}, user="postgres")
    _local_sudo('psql --dbname %(dbname)s < /tmp/%(dumpname)s' % {"dbname":env.db_name, "dumpname":dumpname}) 

def sync_mysql_db():
    dumpname = "db_%s_%s.sql" % (env.db_name, datetime.now().isoformat())
    sudo("mysqldump -u %(user)s -p%(password)s %(dbname)s > /tmp/%(dumpname)s" % {"user": env.db_user, "password": env.db_password, "dbname": env.db_name, "dumpname": dumpname}, user="mysql")
    _get_db(dumpname)
    local('mysqladmin -u %(user)s -p%(password)s drop %(dbname)s -f' % {"user": env.local_db_user, "password": env.local_db_password, "dbname": env.db_name})
    local('mysqladmin -u %(user)s -p%(password)s create %(dbname)s' % {"user": env.local_db_user, "password": env.local_db_password, "dbname": env.db_name})
    local('mysql -u %(user)s -p%(password)s %(dbname)s < /tmp/%(dumpname)s' % {"dbname":env.db_name, "dumpname":dumpname, "user": env.local_db_user, "password": env.local_db_password})

def sync_db():
    """ Copies a database to your local machine. """
    require('config', provided_by=('malawi', 'malawi_old'))
    if not console.confirm('Are you sure you want to wipe out the local %s database?' % env.db_name,
                               default=False):
        utils.abort('Deployment aborted.')
    if env.db_type == "mysql":
        env.db_password = prompt("Password for remote %s database (user: %s): " % (env.db_name, env.db_user))
        env.local_db_password = prompt("Password for local %s database (user: %s): " % (env.db_name, env.db_user))
        sync_mysql_db()
    elif env.db_type == "postgres":
        sync_postgres_db()

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
            sudo('pip install -r %s' % _join(env.code_dir, "requirements.txt"))

def bootstrap(subdir='logistics_project'):
    """ run this after you've checked out the code """
    with cd(env.code_dir):
        update_requirements()
        with cd(subdir):
            with enter_virtualenv():
                run('./manage.py syncdb --noinput')
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
            run('git remote prune origin')
            run('git fetch')
            run('git checkout %(branch)s' % {"branch": env.branch})
            run('git pull %(repo)s %(branch)s' % {"repo": env.remote, "branch": env.branch})
            # cleanup pyc files
            run("find . -name '*.pyc' -delete")
    if env.db_cleanup:
        if not console.confirm('Are you sure you want to wipe out the database?',
                               default=False):
            utils.abort('Deployment aborted.')
        sudo('dropdb %(dbname)s' % {"dbname": env.db_name}, user="postgres")
        sudo('createdb %(dbname)s' % {"dbname": env.db_name}, user="postgres")
        
    bootstrap(subdir='logistics_project')
    if env.stop_start:
        sudo("/etc/init.d/apache2 reload")
        sudo("supervisorctl start all")
        # sudo("service memcached restart")
    

def test_and_deploy():
    django_tests()
    deploy()

