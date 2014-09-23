This is a RapidSMS project to reinforce existing logistics management systems through the use of text messaging. 

NON-PYTHON DEPENDENCIES
* git
* postgres
* pip
* couchdb
* wkhtmltopdf (for pdf report functionality only)
* other dev stuff (see below)

You can install all of the above by running:
```
sudo apt-get update
sudo apt-get install git-core postgresql python-psycopg2 couchdb python-pip libpq-dev python-dev
```
Install pip >=0.6.3. Don't use apt-get on Lucid, it'll give you 0.3.1

DB SETUP

* Change authentication method from ident to MD5 in /etc/postgresql/8.4/main/pg_hba.conf 
* Restart postgres
* Set up a postgres user with the appropriate username and password
* Create the DB

SETUP
```
git clone git://github.com/dimagi/logistics.git
git checkout tz-master
git submodule update --init --recursive
pip install -r deploy/tanzania/prod-requirements.txt
cd logistics_project
cp localsettings.py.example localsettings.py
./manage.py syncdb
./manage.py migrate

# update relevant settings in settings.py or localsettings.py
** most notably, use real email credentials
* sudo /etc/init.d.couchdb start
* ./manage.py celeryd &
* ./manage.py runserver &
```

NOTES
* You might need to remove the distribute install line from the prod-requirements.txt file if you get weird pip errors

## Running Tests

The tests expect that your default language will be English. In order to set this, you may have to add
the following line to your `localsettings.py`:

```
LANGUAGES = (
  ('en', 'English'),
  ('sw', 'Swahili'),
)

LANGUAGE_CODE = "en"
```

You should also disable south migrations by adding the following to localsettings:

```
SOUTH_TESTS_MIGRATE = False
```

Finally, only run the tests for the tanzania app, by running:

```
./manage.py test logistics_project.apps.tanzania
```

## Supported Operating Systems

Ubuntu Lucid Lynx 10.0.4 LTS
Ubuntu 12.0.4 LTS


