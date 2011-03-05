This is a RapidSMS project to reinforce existing logistics management systems through the use of text messaging. 

SETUP
* git clone git://github.com/dimagi/logistics.git
* cd logistics
* fab test update_requirements
* cp localsettings.py.example localsettings.py
* fab test bootstrap
* ./manage.py runserver &
* ./manage.py runrouter &

