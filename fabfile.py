from __future__ import with_statement
from __future__ import unicode_literals
import os

from fabric.api import *
from subprocess import Popen

PATH_SEP = "/"  # necessary to deploy from windows to *nix

env.remote = "origin"
env.branch = "master"
env.pathhack = False

VIRTUALENV_HOME = '/home/dimagi/.virtualenvs/cstock/bin'
PIP = f'{VIRTUALENV_HOME}/pip'
PYTHON = f'{VIRTUALENV_HOME}/python'


def _join(*args):
    if env.pathhack:
        return PATH_SEP.join(args)
    else:
        return os.path.join(*args)


def malawi():
    """
    Malawi configuration (vmracks)
    """
    env.deploy_dir = '/home/dimagi/src'
    env.hosts = ['dimagi@10.84.168.89']
    env.pathhack = True  # sketchily, this must come before any join calls
    env.config = 'malawi'
    env.code_dir = _join(env.deploy_dir, 'logistics')
    env.branch = "malawi-dev"


def _local_sudo(command, user=None):
    if user:
        return Popen("sudo %s" % command, shell=True)
    else:
        return Popen("sudo -u %s %s" % (user, command), shell=True)

def update_requirements():
    """ update external dependencies """
    with cd(env.code_dir):
        sudo(f'{PIP} install -r {_join(env.code_dir, "requirements.txt")}')


def bootstrap():
    """ run this after you've checked out the code """
    with cd(env.code_dir):
        update_requirements()
        run(f'{PYTHON} manage.py migrate --noinput')
        run(f'{PYTHON} manage.py collectstatic --noinput')


def deploy():
    """ deploy code to some remote environment """
    require('config', provided_by=('malawi'))
    sudo("supervisorctl stop all")
    with cd(env.code_dir):
        run('git remote prune origin')
        run('git fetch')
        run('git checkout %(branch)s' % {"branch": env.branch})
        run('git pull %(repo)s %(branch)s' % {"repo": env.remote, "branch": env.branch})
        # cleanup pyc files
        run("find . -name '*.pyc' -delete")

    bootstrap()
    sudo("supervisorctl start all")
