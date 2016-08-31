This is a RapidSMS project to reinforce existing logistics management systems through the use of text messaging. 

NON-PYTHON DEPENDENCIES
* git
* postgres
* pip
* couchdb
* wkhtmltopdf (for pdf report functionality only)

You can install all of the above by running:
> sudo apt-get install git-core postgresql python-psycopg2 couchdb

DB SETUP
* Change authentication method from ident to MD5 in /etc/postgresql/8.4/main/pg_hba.conf 
* Restart postgres
* Set up a postgres user with the appropriate username and password
* Create the DB

SETUP
* git clone git://github.com/dimagi/logistics.git
* cd logistics
* pip install -r pip-requires.txt
* git submodule init
* git submodule update
* cd logistics_project
* cp localsettings.py.example localsettings.py
* update relevant settings in settings.py or localsettings.py
  * set 'DEBUG = True' to get static files to work
  * most notably, use real email credentials
* ./manage.py syncdb
* ./manage.py migrate (see note below about troubleshooting migrations)
* python import_facilities.py Facilities.csv
* sudo /etc/init.d.couchdb start
* ./manage.py celeryd &
* ./manage.py runserver &
* ./manage.py runrouter &


SUPPORTED OPERATING SYSTEM
Ubuntu Lucid Lynx 10.0.4 LTS

## Troubleshooting install

# South migration fails
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