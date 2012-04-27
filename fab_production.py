"""
Server layout:
    ~/services/
        This contains two subfolders
            /apache/
            /supervisor/
        which hold the configurations for these applications
        for each environment (staging, demo, etc) running on the server.
        Theses folders are included in the global /etc/apache2 and
        /etc/supervisor configurations.

    ~/www/
        This folder contains the code, python environment, and logs
        for each environment (staging, demo, etc) running on the server.
        Each environment has its own subfolder named for its evironment
        (i.e. ~/www/staging/logs and ~/www/demo/logs).
"""

import os, sys

from fabric.api import *
from fabric.contrib import files, console
from fabric.contrib.project import rsync_project
from fabric import utils
from fabric.decorators import hosts
import posixpath


PROJECT_ROOT = os.path.dirname(__file__)
RSYNC_EXCLUDE = (
    '.DS_Store',
    '.git',
    '*.pyc',
    '*.example',
    '*.db',
)
env.home = '/home/ilsgateway'
env.project = 'logistics_project'
env.code_repo = 'git://github.com/dimagi/logistics.git'


def _setup_path():
    # using posixpath to ensure unix style slashes. See bug-ticket: http://code.fabfile.org/attachments/61/posixpath.patch
    env.root = posixpath.join(env.home, 'www', env.environment)
    env.log_dir = posixpath.join(env.home, 'www', env.environment, 'log')
    env.code_root = posixpath.join(env.root, 'code_root')
    env.project_root = posixpath.join(env.code_root, env.project)
    env.project_media = posixpath.join(env.code_root, 'media')
    env.project_static = posixpath.join(env.project_root, 'static')
    env.virtualenv_root = posixpath.join(env.root, 'python_env')
    env.services = posixpath.join(env.home, 'services')


def setup_dirs():
    """ create (if necessary) and make writable uploaded media, log, etc. directories """
    sudo('mkdir -p %(log_dir)s' % env, user=env.sudo_user)
    sudo('chmod a+w %(log_dir)s' % env, user=env.sudo_user)
    # sudo('mkdir -p %(project_media)s' % env, user=env.sudo_user)
    # sudo('chmod a+w %(project_media)s' % env, user=env.sudo_user)
    # sudo('mkdir -p %(project_static)s' % env, user=env.sudo_user)
    sudo('mkdir -p %(services)s/apache' % env, user=env.sudo_user)
    sudo('mkdir -p %(services)s/supervisor' % env, user=env.sudo_user)


def staging():
    """ use staging environment on remote host"""
    env.code_branch = 'tz-master'
    env.sudo_user = 'ilsgateway'
    env.environment = 'staging'
    env.server_port = '9002'
    env.server_name = 'noneset'
    env.hosts = ['ilsgateway@108.166.86.217']
    env.settings = '%(project)s.settings' % env
    env.db = '%s_%s' % (env.project, env.environment)
    _setup_path()


def production():
    """ use production environment on remote host"""
    env.code_branch = 'tz-master'
    env.sudo_user = 'ilsgateway'
    env.environment = 'production'
    env.server_port = '9010'
    env.server_name = 'ilsgateway-production'
    env.hosts = ['ilsgateway@184.106.171.98']
    env.settings = '%(project)s.settings' % env
    env.db = '%s_%s' % (env.project, env.environment)
    _setup_path()

#    env.code_branch = 'master'
#    env.sudo_user = 'aremind'
#    env.environment = 'production'
#    env.hosts = []
#    raise NotImplementedError()


def install_packages():
    """Install packages, given a list of package names"""

    require('environment', provided_by=('staging', 'production'))
    packages_file = posixpath.join(PROJECT_ROOT, 'requirements', 'apt-packages.txt')
    with open(packages_file) as f:
        packages = f.readlines()
    sudo("apt-get install -y %s" % " ".join(map(lambda x: x.strip('\n\r'), packages)))


def upgrade_packages():
    """Bring all the installed packages up to date"""
    pass
#    require('environment', provided_by=('staging', 'production'))
#    sudo("apt-get update -y")
#    sudo("apt-get upgrade -y")


def setup_server():
    """Set up a server for the first time in preparation for deployments."""

    require('environment', provided_by=('staging', 'production'))
    upgrade_packages()
    # Install required system packages for deployment, plus some extras
    # Install pip, and use it to install virtualenv
    install_packages()
    sudo("easy_install -U pip")
    sudo("pip install -U virtualenv")
    upgrade_packages()
#    create_db_user() //this needs to be done by hand as we are doing a data migration.
#    create_db()


def create_db_user():
    """Create the Postgres user."""

    require('environment', provided_by=('staging', 'production'))
    sudo('createuser -D -A -R %(sudo_user)s' % env, user='postgres')


def create_db():
    """Create the Postgres database."""

    require('environment', provided_by=('staging', 'production'))
    sudo('createdb -O %(sudo_user)s %(db)s' % env, user='postgres')


def bootstrap():
    """ initialize remote host environment (virtualenv, deploy, update) """
    require('root', provided_by=('staging', 'production'))
    sudo('mkdir -p %(root)s' % env, user=env.sudo_user)
    clone_repo()
    setup_dirs()
    update_services()
    create_virtualenv()
    update_requirements()
#    setup_translation()
    fix_locale_perms()


def create_virtualenv():
    """ setup virtualenv on remote host """
    require('virtualenv_root', provided_by=('staging', 'production'))
    args = '--clear --distribute --no-site-packages'
    sudo('virtualenv %s %s' % (args, env.virtualenv_root), user=env.sudo_user)


def clone_repo():
    """ clone a new copy of the git repository """
    with cd(env.root):
        sudo('git clone %(code_repo)s %(code_root)s' % env, user=env.sudo_user)


def deploy():
    """ deploy code to remote host by checking out the latest via git """
    require('root', provided_by=('staging', 'production'))
    sudo('echo ping!') #hack/workaround for delayed console response
    if env.environment == 'production':
        if not console.confirm('Are you sure you want to deploy production?',
                               default=False):
            utils.abort('Production deployment aborted.')
    with settings(warn_only=True):
        stop()
    try:
        with cd(env.code_root):
            sudo('git checkout %(code_branch)s' % env, user=env.sudo_user)
            sudo('git pull', user=env.sudo_user)
            sudo('git submodule init', user=env.sudo_user)
            sudo('git submodule update', user=env.sudo_user)
        #update_requirements()
        migrate()
        load_data()
        collectstatic()
        
    finally:
        # hopefully bring the server back to life if anything goes wrong
        start()


def update_requirements():
    """ update external dependencies on remote host """
    require('code_root', provided_by=('staging', 'production'))
    requirements = posixpath.join(env.code_root, 'requirements')
    with cd(requirements):
        cmd = ['sudo -u %s -H pip install' % env.sudo_user]
        cmd += ['-E %(virtualenv_root)s' % env]
        cmd += ['--requirement %s' % posixpath.join(requirements, 'apps.txt')]
        run(' '.join(cmd))


def update_services():
    """ upload changes to services such as nginx """

    with settings(warn_only=True):
        stop()
    upload_supervisor_conf()
    upload_apache_conf()
    start()
    netstat_plnt()


def configtest():    
    """ test Apache configuration """
    require('root', provided_by=('staging', 'production'))
    run('apache2ctl configtest')


def apache_reload():    
    """ reload Apache on remote host """
    require('root', provided_by=('staging', 'production'))
    run('sudo /etc/init.d/apache2 reload')


def apache_restart():
    """ restart Apache on remote host """
    require('root', provided_by=('staging', 'production'))
    run('sudo /etc/init.d/apache2 restart')


def netstat_plnt():
    """ run netstat -plnt on a remote host """
    require('hosts', provided_by=('production', 'staging'))
    run('sudo netstat -plnt')


def stop():
    """ stop server and celery on remote host """
    require('environment', provided_by=('staging', 'demo', 'production'))
    _supervisor_command('stop %(project)s-%(environment)s:*' % env)


def start():
    """ start server and celery on remote host """
    require('environment', provided_by=('staging', 'demo', 'production'))
    _supervisor_command('start %(project)s-%(environment)s:*' % env)


def servers_start():
    ''' Start the gunicorn servers '''
    require('environment', provided_by=('staging', 'demo', 'production'))
    _supervisor_command('start  %(project)s-%(environment)s:%(project)s-%(environment)s-server' % env)


def servers_stop():
    ''' Stop the gunicorn servers '''
    require('environment', provided_by=('staging', 'demo', 'production'))
    _supervisor_command('stop  %(project)s-%(environment)s:%(project)s-%(environment)s-server' % env)


def servers_restart():
    ''' Start the gunicorn servers '''
    require('environment', provided_by=('staging', 'demo', 'production'))
    _supervisor_command('restart  %(project)s-%(environment)s:%(project)s-%(environment)s-server' % env)


def migrate():
    """ run south migration on remote environment """
    require('project_root', provided_by=('production', 'demo', 'staging'))
    with cd(env.project_root):
        run('%(virtualenv_root)s/bin/python manage.py syncdb --noinput --settings=%(settings)s' % env)
        run('%(virtualenv_root)s/bin/python manage.py migrate --noinput --settings=%(settings)s' % env)


def collectstatic():
    """ run collectstatic on remote environment """
    require('project_root', provided_by=('production', 'demo', 'staging'))
    with cd(env.project_root):
        sudo('%(virtualenv_root)s/bin/python manage.py collectstatic --noinput --settings=%(settings)s' % env, user=env.sudo_user)


def load_data():
    """
    Loads data specific to TZ. 
    """
    require('project_root', provided_by=('production', 'demo', 'staging'))
    with cd(env.project_root):
        sudo('%(virtualenv_root)s/bin/python manage.py tz_update_schedules --settings=%(settings)s' % env, user=env.sudo_user)


#def reset_local_db():
#    """ Reset local database from remote host """
#    require('code_root', provided_by=('production', 'staging'))
#    if env.environment == 'production':
#        utils.abort('Local DB reset is for staging environment only')
#    question = 'Are you sure you want to reset your local ' \
#               'database with the %(environment)s database?' % env
#    sys.path.append('.')
#    if not console.confirm(question, default=False):
#        utils.abort('Local database reset aborted.')
#    if env.environment == 'staging':
#        from aremind.settings_staging import DATABASES as remote
#    else:
#        from aremind.settings_production import DATABASES as remote
#    from aremind.localsettings import DATABASES as loc
#    local_db = loc['default']['NAME']
#    remote_db = remote['default']['NAME']
#    with settings(warn_only=True):
#        local('dropdb %s' % local_db)
#    local('createdb %s' % local_db)
#    host = '%s@%s' % (env.user, env.hosts[0])
#    local('ssh -C %s sudo -u aremind pg_dump -Ox %s | psql %s' % (host, remote_db, local_db))

#
#def setup_translation():
#    """ Setup the git config for commiting .po files on the server """
#    run('sudo -H -u %s git config --global user.name "aremind Translators"' % env.sudo_user)
#    run('sudo -H -u %s git config --global user.email "aremind-dev@dimagi.com"' % env.sudo_user)


def fix_locale_perms():
    """ Fix the permissions on the locale directory """
    require('root', provided_by=('staging', 'production'))
    locale_dir = '%s/aremind/locale/' % env.code_root
    run('sudo chown -R %s %s' % (env.sudo_user, locale_dir))
    run('sudo chgrp -R www-data %s' % locale_dir)
    run('sudo chmod -R g+w %s' % locale_dir)


#def commit_locale_changes():
#    """ Commit locale changes on the remote server and pull them in locally """
#    fix_locale_perms()
#    with cd(env.code_root):
#        run('sudo -H -u %s git add aremind/locale' % env.sudo_user)
#        run('sudo -H -u %s git commit -m "updating translation"' % env.sudo_user)
#    local('git pull ssh://%s%s' % (env.host, env.code_root))
#

def upload_supervisor_conf():
    """Upload and link Supervisor configuration from the template."""
    require('environment', provided_by=('staging', 'demo', 'production'))
    template = posixpath.join(os.path.dirname(__file__), 'services', 'templates', 'supervisor.conf')
    destination = '/var/tmp/supervisor.conf'
    files.upload_template(template, destination, context=env, use_sudo=True)
    enabled =  posixpath.join(env.services, u'supervisor/%(environment)s.conf' % env)
    run('sudo chown -R %s %s' % (env.sudo_user, destination))
    run('sudo chgrp -R www-data %s' % destination)
    run('sudo chmod -R g+w %s' % destination)
    run('sudo -u %s mv -f %s %s' % (env.sudo_user, destination, enabled))
    _supervisor_command('update')


def upload_apache_conf():
    """Upload and link Supervisor configuration from the template."""
    require('environment', provided_by=('staging', 'demo', 'production'))
    template = posixpath.join(os.path.dirname(__file__), 'services', 'templates', 'apache.conf')
    destination = '/var/tmp/apache.conf'
    files.upload_template(template, destination, context=env, use_sudo=True)
    enabled =  posixpath.join(env.services, u'apache/%(environment)s.conf' % env)
    run('sudo chown -R %s %s' % (env.sudo_user, destination))
    run('sudo chgrp -R www-data %s' % destination)
    run('sudo chmod -R g+w %s' % destination)
    run('sudo -u %s mv -f %s %s' % (env.sudo_user, destination, enabled))
    apache_reload()


def _supervisor_command(command):
    require('hosts', provided_by=('staging', 'production'))
    run('sudo supervisorctl %s' % command)
