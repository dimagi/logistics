This is a RapidSMS project to reinforce existing logistics management systems through the use of text messaging. 

NON-PYTHON DEPENDENCIES
* git
* postgres
* pip
* couchdb

You can install all of the above by running:
> sudo apt-get install git-core postgresql python-psycopg2 couchdb

Install Django 1.2. Don't use apt-get on Lucid, it'll give you 1.1
Install pip >=0.6.3. Don't use apt-get on Lucid, it'll give you 0.3.1

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
* cd logistics
* cp localsettings.py.example localsettings.py
* ./manage.py syncdb
* ./manage.py migrate
* python import_facilities.py Facilities.csv
* update relevant settings in settings.py or localsettings.py
** most notably, use real email credentials
* sudo /etc/init.d.couchdb start
* ./manage.py celeryd &
* ./manage.py runserver &
* ./manage.py runrouter &


SUPPORTED OPERATING SYSTEM
Ubuntu Lucid Lynx 10.0.4 LTS


