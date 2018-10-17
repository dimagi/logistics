This is a RapidSMS project to reinforce existing logistics management systems through the use of text messaging.

This readme is specific to the cstock project.

# Installation

NON-PYTHON DEPENDENCIES
* git
* pip
* couchdb

You can install all of the above by running:
```
> sudo apt-get install git-core couchdb
```

## Code installation

The following sets up the code

```
git clone git://github.com/dimagi/logistics.git
cd logistics
pip install -r pip-requires.txt
git submodule init
git submodule update
cd logistics_project
cp localsettings.py.example localsettings.py
update relevant settings in settings.py or localsettings.py
```


## DB Setup

Recommended database is MySQL.

Install it as normal, create a database and update `localsettings.py` accordingly to connect.

Because this is a sad legacy project and the migration history is messed up,
the best way to get a local DB running is to start with the production schema.

To do this, setup mysql as per above and then run the following commands:

```
mysql -u root -p cstock < db_schema/cstock_schema_2018-10-17.sql
cd logistics_project
./manage.py migrate --fake
```

The first command syncs the production schema (as of October 2018) and the second fakes all migrations.
You should be able to develop in parallel with production after that and use south / `./manage.py migrate` 
for future DB schema changes.


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

# Legacy information

**Note that the reamainder of this README is likely out of date**


SUPPORTED OPERATING SYSTEM
Ubuntu Lucid Lynx 10.0.4 LTS

## Troubleshooting install

### South migration fails
There is a circular dependency in the South migrations. This is the workaround:

 * open logistics_project/deployments/malawi/migrations/logistics/0001_initial.py
 * comment out the section in 'forwards' that creates the 'logistics_stockrequest' table
 * run the migration: ./manage.py migrate logistics 0001
 * delete the migration record from the database
   * DELETE FROM south_migrationhistory WHERE app_name = 'logistics' and migration = '0001_initial';
 * run the rapidsms migrations: ./manage.py migrate rapidsms
 * in the logisitics/0001_initial.py file un-comment the section that creates the 'logistics_stockrequest' table
   but comment out everything else in the 'forward' method.
 * run the migration: ./manage.py migrate logistics 0001
 * run ./manage.py migrate
