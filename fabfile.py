from __future__ import with_statement
from __future__ import unicode_literals

from fabric.api import *

env.remote = "origin"
env.branch = "master"

VIRTUALENV_HOME = '/home/dimagi/.virtualenvs/cstock/bin'
PIP = f'{VIRTUALENV_HOME}/pip'
PYTHON = f'{VIRTUALENV_HOME}/python'


def malawi():
    """
    Malawi configuration
    """
    env.deploy_dir = '/home/dimagi/src'
    env.hosts = ['dimagi@10.84.168.89']
    env.code_dir = f'{env.deploy_dir}/logistics'
    env.branch = "malawi-dev"


def update_requirements():
    sudo(f'{PIP} install -r {env.code_dir}/requirements.txt')


def django_stuff():
    run(f'{PYTHON} manage.py migrate --noinput')
    run(f'{PYTHON} manage.py collectstatic --noinput')


def update_code():
    run('git remote prune origin')
    run('git fetch')
    run('git checkout %(branch)s' % {"branch": env.branch})
    run('git pull %(repo)s %(branch)s' % {"repo": env.remote, "branch": env.branch})
    # cleanup pyc files
    run("find . -name '*.pyc' -delete")


def deploy():
    """ deploy code to some remote environment """
    sudo("supervisorctl stop all")
    with cd(env.code_dir):
        update_code()
        update_requirements()
        django_stuff()
    sudo("supervisorctl start all")
