from fabric.api import *


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
    env.branch = "main"


def update_code():
    run('git remote prune origin')
    run('git fetch')
    run(f'git checkout {env.branch}')
    run(f'git pull origin {env.branch}')
    run("find . -name '*.pyc' -delete")  # cleanup pyc files


def update_requirements():
    sudo(f'{PIP} install -r {env.code_dir}/requirements.txt')


def django_stuff():
    run(f'{PYTHON} manage.py migrate --noinput')
    run(f'{PYTHON} manage.py collectstatic --noinput')


def deploy():
    """
    Deploy latest changes
    """
    sudo("supervisorctl stop all")
    with cd(env.code_dir):
        update_code()
        update_requirements()
        django_stuff()
    sudo("supervisorctl start all")
