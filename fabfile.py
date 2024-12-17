import datetime
import posixpath

from fabric import task

"""
To use this file, first `pip install fabric` then run:

fab -H cstock@10.10.100.77 deploy --prompt-for-sudo-password
"""

CODE_ROOT = "/home/cstock/www/cstock/code_root/"
VIRTUALENV_ROOT = '/home/cstock/.virtualenvs/cstock/'
BRANCH = "main"


@task
def deploy(c):
    """
    Deploy code to remote host by checking out the latest via git.
    """
    start = datetime.datetime.now()
    update_code(c)
    update_virtualenv(c)
    django_stuff(c)
    services_restart(c)
    print(f"deploy completed in {datetime.datetime.now() - start}")


def update_code(c):
    print("updating code...")
    with c.cd(CODE_ROOT):
        c.run("git fetch")
        c.run(f"git checkout {BRANCH}")
        c.run(f"git reset --hard origin/{BRANCH}")
        c.run("find . -name '*.pyc' -delete")


def update_virtualenv(c):
    """
    Update external dependencies on remote host assumes you've done a code update.
    """
    print("updating requirements...")
    files = (
        posixpath.join(CODE_ROOT, "requirements.txt"),
    )
    with c.prefix("source {}/bin/activate".format(VIRTUALENV_ROOT)):
        for req_file in files:
            c.run("pip install -r {}".format(req_file))


def django_stuff(c):
    """
    staticfiles, migrate, etc.
    """
    print("Running migrations and building staticfiles...")
    with c.cd(CODE_ROOT):
        c.run("{}/bin/python manage.py migrate".format(VIRTUALENV_ROOT))
        c.run("{}/bin/python manage.py collectstatic --noinput".format(VIRTUALENV_ROOT))


def services_restart(c):
    print("Restarting services...")
    c.sudo("sudo supervisorctl stop all")
    c.sudo("sudo supervisorctl start all")
