This is a RapidSMS project to reinforce existing logistics management systems through the use of text messaging. 

NON-PYTHON DEPENDENCIES
* git
* postgres
* pip
* couchdb
* wkhtmltopdf (for pdf report functionality only)

You can install all of the above by running:
```
sudo apt-get install git-core postgresql python-psycopg2 couchdb python-pip
```
Install pip >=0.6.3. Don't use apt-get on Lucid, it'll give you 0.3.1

DB SETUP
* Change authentication method from ident to MD5 in /etc/postgresql/8.4/main/pg_hba.conf 
* Restart postgres
* Set up a postgres user with the appropriate username and password
* Create the DB

SETUP
* git clone git://github.com/dimagi/logistics.git
* cd logistics/deploy/tanzania
* pip install -r prod-requirements.txt
* cd ../..
* git submodule init
* git submodule update
* cd logistics_project
* cp localsettings.py.example localsettings.py
* ./manage.py syncdb
* ./manage.py migrate
* update relevant settings in settings.py or localsettings.py
** most notably, use real email credentials
* sudo /etc/init.d.couchdb start
* ./manage.py celeryd &
* ./manage.py runserver &

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

Because the threadless router doesn't play nice with initiation of outbound messages in the tests you have
to make one modification to the code to get the tests to pass. Comment out the following line in
`logistics_project.apps.tanzania.reminders.send_message` so that it looks like the following:

```
def send_message(contact, message, **kwargs):
    # this hack sets the global router to threadless router.
    # should maybe be cleaned up.
    # router.router = Router()   # <---- this line commented out
    contact.message(message, **kwargs)
```


## Supported Operating Systems

Ubuntu Lucid Lynx 10.0.4 LTS
Ubuntu 12.0.4 LTS


