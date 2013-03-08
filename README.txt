This is a RapidSMS project to reinforce existing logistics management systems through the use of text messaging. 

NON-PYTHON DEPENDENCIES
* git
* postgres
* pip
* couchdb
* wkhtmltopdf (for pdf report functionality only)

You can install all of the above by running:
> sudo apt-get install git-core postgresql python-psycopg2 couchdb memcached

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
* update relevant settings in settings.py or localsettings.py
** most notably, use real email credentials
* sudo /etc/init.d.couchdb start
* ./manage.py celeryd &
* ./manage.py runserver &
* ./manage.py runrouter &

ENABLING COUCH-LUCENE
To enable full-text search on the couch models, you'll need to set up couch-lucene. Follow these instructions: https://github.com/rnewson/couchdb-lucene. Basically:
* install java
  * sudo add-apt-repository "deb http://archive.canonical.com/ lucid partner"
  * sudo apt-get update
  * sudo apt-get install sun-java6-jre sun-java6-plugin
  * sudo update-alternatives --config java
* apt-get install maven2
* git pull https://github.com/rnewson/couchdb-lucene, mvn, unzip target, and run
* configure couchdb settings 
* syncdb to install the index views
* done!

SUPPORTED OPERATING SYSTEM
Ubuntu Lucid Lynx 10.0.4 LTS

CODE LAYOUT
The goal of this project setup was to reuse code among different logistics deployments which also supported custom reports and dashboards. Between deployments, the 'switch' is flipped by importing different settings in localsettings.py. Most apps are shared, although truly deployment-specific code lives in a deployment specific app (i.e. ewsghana app, tanzania app, malawi app). Future contributors should aim to put all generic code in the shared apps and minimize contributions to the deployment-specific app.
