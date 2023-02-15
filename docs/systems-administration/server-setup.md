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

# Set up cstock

Set up cstock code according to the [Dev Setup Instructions](../dev-setup.md).

As the *cstock* user, set up your code directory and Python environment:

```
mkdir -p ~/www/cstock/
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
