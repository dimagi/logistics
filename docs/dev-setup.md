Setting up a development environment
====================================

## Install prerequisites

Before getting started you will need to install:

- [Python 3.8](https://www.python.org/downloads/)
- [Virtualenv](https://virtualenv.pypa.io/en/stable/) and [Virtualenvwrapper](https://virtualenvwrapper.readthedocs.io/en/latest/)
- [git](https://git-scm.com/downloads)
- [MySQL 5.7](https://dev.mysql.com/downloads/mysql/5.7.html)

## Download the code

```
git clone https://github.com/dimagi/logistics.git
```

## Setup the Python virtual environment

```
mkvirtualenv cstock -p $(which python3.8)
```

Then in the code root directory, run:

```
pip install -r requirements.txt
```

## Create the database

Connect to your MySQL DB and run the following:

```
CREATE DATABASE cstock;
```

## Configure project settings

First create your localsettings file:

```
cp logistics_project/localsettings.py.example logistics_project/localsettings.py
```

Then edit the file so that the `DATABASES` value has the right databsae name and credentials for your local MySQL.

## Initialize the Database

Run this to set up the database tables:

```
./manage.py migrate
```

Then create some helper data:

```
./manage.py loaddata data/cstock-locations.json
./manage.py loaddata data/cstock-logistics.json
```

## Create a superuser

Run the following command and fill in the prompts:

```
./manage.py createsuperuser
```

## Run the server

Start the server with: 

```
./manage.py createsuperuser
```

You should be able to login to the dashboard with the user you just created.


## (Optional) Run celery and SMS router

The `runrouter` process is necessary for SMS-related functionality.
Celery is required for scheduled SMS reminders as well as for background jobs that update the data warehouse.

```
./manage.py runrouter
celery -A logistics_project worker -l info
```

## Testing

You can run individual tests using the following syntax:

```
./manage.py test logistics_project.apps.malawi.tests.transfer.TestTransfer
```
