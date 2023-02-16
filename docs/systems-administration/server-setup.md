Server Installation
===================

These steps are from a production installation.

# Create a system user

Fill in the prompts after running the command:

```
adduser cstock
```

This user will be the one to run cstock and other related processes.

# Install and configure MySQL

Follow [this guide](https://www.digitalocean.com/community/tutorials/how-to-install-mysql-on-ubuntu-20-04) to install MySQL.

```
sudo apt install mysql-server
sudo systemctl start mysql.service
```

## Set a root login/password

Replace the password with the one you want to set. 

```
$ sudo mysql
mysql> ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY '***';
mysql> \q
$ mysql -u root -p
mysql> ALTER USER 'root'@'localhost' IDENTIFIED WITH auth_socket;
mysql> \q
```

## Secure installation

```
sudo mysql_secure_installation
```

## Create cstock database user

Don't forget to change the password!

```
$ sudo mysql
mysql> CREATE USER 'cstock'@'localhost' IDENTIFIED WITH mysql_native_password BY '***';
mysql> GRANT CREATE, ALTER, DROP, INSERT, UPDATE, INDEX, DELETE, SELECT, REFERENCES, RELOAD on *.* TO 'cstock'@'localhost' WITH GRANT OPTION;
mysql> \q
```

## Create cstock database

```
$ mysql -u cstock -p
mysql> CREATE DATABASE cstock;
mysql> \q
```

# Restore cstock database

Get a database backup and copy it to the server using `rsync`:

```
rsync -P -e ssh cstock_2023-02-08_06h25m.Wednesday.sql.gz root@cstock.codero:
```

When it completes, unzip and restore it:

```
gunzip cstock_2023-02-08_06h25m.Wednesday.sql.gz
mysql < cstock_2023-02-08_06h25m.Wednesday.sql
```

Note: the above restore had to be run as root due to permissions issues.


# Install Python 3.9, pip, virtualenv, virtualenvwrapper, mysql dependencies

```
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.9 python3.9-dev libmysqlclient-dev
sudo apt install python3-pip
python -m pip install --user virtualenv virtualenvwrapper
```

# Set up virtualenvewrapper

```
source /home/cstock/.local/bin/virtualenvwrapper.sh
```

If you run into errors, check your environment variables and update your `.profile` as described
[here](https://askubuntu.com/a/995130) and [here](https://virtualenvwrapper.readthedocs.io/en/latest/).

# Install Redis

Following [this guide](https://www.digitalocean.com/community/tutorials/how-to-install-and-secure-redis-on-ubuntu-20-04).

```
sudo apt install redis-server
```

Then change `/etc/redis/redis.conf` to have

```
supervised systemd
```

As described in the article.

None of the other steps are required.

# Create project directories

As the *cstock* user, set up your project directories:

```
mkdir -p ~/www/cstock/
mkdir -p ~/www/cstock/log/
```

# Set up cstock

Set up cstock code according to the [Dev Setup Instructions](../dev-setup.md).

As the *cstock* user, set up your code directory and Python environment:

```
cd ~/www/cstock/
git clone https://github.com/dimagi/logistics.git code_root
cd code_root
mkvirtualenv -p python3.9 cstock
setvirtualenvproject
pip install -r requirements.txt
```

## Configure localsettings

Copy your localsettings across from the previous production project and edit anything relevant
(e.g. database credentials)

**If you are able to run `./manage.py runserver` with no issues, things are likely working as expected.**

# Install and configure nginx

By following [this guide](https://www.digitalocean.com/community/tutorials/how-to-install-nginx-on-ubuntu-20-04).

Then create a new site in `/etc/nginx/sites-available/` based off the following.
You will have to adjust hosts, ports, and file paths to match your setup.

```
upstream cstock {
  # fail_timeout=0 means we always retry an upstream even if it failed
  # to return a good HTTP response (in case the Unicorn master nukes a
  # single worker for timing out).
  server localhost:9095 fail_timeout=0;
}

server {
  listen 80;
  listen [::]:80;

  server_name cstock.jsi.com;

  # don't forward traffic from unexpected hosts.
  # this prevents a flood of django.security.DisallowedHost errors from bots/spammers, etc.
  if ($host !~* ^(cstock.jsi.com|localhost|127.0.0.1)$ ) {
    return 444;
  }


  # Serve static files from nginx
  location /static/ {
    alias  /home/cstock/www/code_root/static_root/;
  }


  location / {

    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header Host $http_host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 300s;
    proxy_redirect off;

    if (!-f $request_filename) {
       proxy_pass http://cstock;
       break;
    }
  }

}
```

## Install and configure supervisord

Follow [these instructions](https://www.digitalocean.com/community/tutorials/how-to-install-and-manage-supervisor-on-ubuntu-and-debian-vps)
to set up supervisord.

```
sudo apt install supervisor
```

Then create a supervisord configuration file that looks something like this.
Save it to `/etc/supervisor/conf.d/cstock.conf`.
Like nginx, you'll have to tweak paths and such.


```
[program:rapidsms-router]
process_name=rapidsms-router
command=/home/cstock/.virtualenvs/cstock/bin/python /home/cstock/www/cstock/code_root/manage.py runrouter 
directory=/home/cstock/www/cstock/code_root/
user=cstock
autostart=true
autorestart=true
stdout_logfile=/home/cstock/www/cstock/log/rapidsms.log
redirect_stderr=true
stderr_logfile=/home/cstock/www/cstock/log/rapidsms.error.log

[program:celery]
;command=/usr/bin/python /usr/local/bin/celery -A logistics_project worker -l info -B
command=/home/cstock/.virtualenvs/cstock/bin/celery -A logistics_project worker -l info -B
directory=/home/cstock/www/cstock/code_root/
user=cstock
numprocs=1
stdout_logfile=/home/cstock/www/cstock/log/celery.log
stderr_logfile=/home/cstock/www/cstock/log/celery.error.log
autostart=true
autorestart=true
startsecs=10
stopwaitsecs = 600
priority=998

[program:gunicorn]
command=/home/cstock/.virtualenvs/cstock/bin/gunicorn -w 4 logistics_project.wsgi --bind 127.0.0.1:9095 --log-file /home/cstock/www/cstock/log/gunicorn.command.log --log-level debug --timeout 300
directory=/home/cstock/www/cstock/code_root/
user=cstock
stdout_logfile=/home/cstock/www/cstock/log/gunicorn.log
stderr_logfile=/home/cstock/www/cstock/log/gunicorn.error.log
autostart=true
autorestart=true
```


# Set up and configure Kannel (SMS gateway)

```
sudo apt install kannel
```

Update your `/etc/kannel/kannel.conf` file based on the example [provided here](https://github.com/dimagi/logistics/blob/main/deploy/kannel/kannel.conf)

You will have to provide appropriate passwords.
