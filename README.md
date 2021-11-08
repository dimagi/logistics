This is a RapidSMS project to reinforce existing logistics management systems through the use of text messaging.

This readme is specific to the cstock project.

# Installation

This project requires Python 2.7.
It's recommended to set it up in a virtual environment.

You'll also need `python-dev` to install requirements:

```
sudp apt install python2.7 python2.7-dev
```

NON-PYTHON DEPENDENCIES
* git
* pip
* couchdb

You can install all of the above by running:

```
> sudo apt-get install git-core couchdb
```

## Code installation

Once you've done that you can run the following to set up the code:

```
git clone git://github.com/dimagi/logistics.git
cd logistics
pip install -r pip-requires.txt
git submodule update --init
cd logistics_project
cp localsettings.py.example localsettings.py
update relevant settings in settings.py or localsettings.py
```

## DB Setup

The recommended database is MySQL, which is used in production.

Install it as normal, create a database and update `localsettings.py` accordingly to connect.

Because this is a sad legacy project and the migration history is messed up,
the best way to get a local DB running is to start with the production schema.

To do this, setup mysql as per above and then run the following commands:

```
mysql -u root -p cstock < data/cstock_schema_2018-10-17.sql
cd logistics_project
./manage.py migrate --fake
```

The first command syncs the production schema (as of October 2018) and the second fakes all migrations.
You should be able to develop in parallel with production after that and use south / `./manage.py migrate` 
for future DB schema changes.

### Loading data

To load some useful production data (locations, products, etc.) run:

```
./manage.py loaddata ../data/cstock-locations.json
./manage.py loaddata ../data/cstock-logistics.json
```

## Running the server

`./manage.py runserver`


### (Optional) Run celery and SMS router

```
./manage.py celeryd
./manage.py runrouter
```

# Testing

This project uses nose for testing. You can run individual tests using the following type of syntax:

```
./manage.py test logistics_project.apps.malawi.tests.transfer:TestTransfer
```

Note that running the entire test suite hangs on apparent database locking issues. You must run subsets of tests at a time.
