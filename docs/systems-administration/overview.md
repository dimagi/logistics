cStock System Overview
======================

[cStock](https://cstock.health.gov.mw/) is a website built and maintained by the Malawi Ministry of Health.
There is a web component as well as an SMS component.

## Hosting

cStock is hosted by the Ministry of Health in a local data center.

## Code

The cStock application code is hosted [on Github](https://github.com/dimagi/logistics/).
It is a Python / Django application, based on RapidSMS.

In general system administrators should not need to modify cStock code,
but it would be necessary to add new features or fix bugs.

To get up and running with the cStock code, see [the development setup documentation](/dev-setup/).

## Key Services

cStock consists of the following key services:

![cStock Architecture](/images/cstock-architecture.png)

In the above, green boxes run custom cStock code, blue boxes are 3rd-party applications running
on the cStock server, and grey boxes are external services.

Here is a high-level description of each cStock service:

| Service                 | Description                                                                                                                     | Technology        |
|-------------------------|---------------------------------------------------------------------------------------------------------------------------------|-------------------|
| Web Application Process | The web application is the business logic that powers the cStock web application.                                               | Django            |
| SMS Application Process | A process that runs alongside the web application to manage SMS workflows                                                       | Django + RapidSMS |
| Background Task Process | A process that runs alongside the web application to manage background tasks and scheduled SMS messages                         | Django + Celery   |
| Database                | The database houses all persistent data.                                                                                        | MySQL             |
| Cache / Message Broker  | The cache is used to improve the performance of the site and pass messages between other processes.                             | Redis             |
| Web Server              | The web server sits in front of the web application, providing outside internet access. It also hosts static files like images. | Nginx             |
| SMS Gateway             | The SMS Gateway connects to third-party SMS providers (TNM and Airtel) and routes the messages to the SMS application process.  | Kannel            |

In general, all of these need to be running and functioning properly for cStock to work.

### Web Application Process

The web application is the business logic that powers the cStock web application.
Here is the key information for it:

| Item                    | Value                                                                                                   | 
|-------------------------|---------------------------------------------------------------------------------------------------------|
| Process                 | Django (Gunicorn)                                                                                       | 
| Log files               | `/home/cstock/www/cstock/log/gunicorn.command.log` and `/home/cstock/www/cstock/log/gunicorn.error.log` |
| Configuration file      | `/home/cstock/www/cstock/code_root/logistics_project/localsettings.py`                                  |
| View status             | `sudo supervisorctl status` (gunicorn process)                                                          |
| Stop / Start / Restart  | `sudo supervisorctl stop gunicorn` (or `start`, or `restart`)                                           |

### SMS Application Process

The SMS web application runs alongside the web application to manage SMS workflows.
Here is the key information for it:

| Item                   | Value                                                                    | 
|------------------------|--------------------------------------------------------------------------|
| Process                | Django (RapidSMS)                                                        | 
| Log files              | `/home/cstock/www/cstock/log/rapidsms.log`                               |
| Configuration file      | `/home/cstock/www/cstock/code_root/logistics_project/localsettings.py`  |
| View status            | `sudo supervisorctl status` (rapidsms-router process)                    |
| Stop / Start / Restart | `sudo supervisorctl stop rapidsms-router` (or `start`, or `restart`)     |

### Background Task Process

The background task process runs alongside the web application to manage background tasks and scheduled SMS messages.
Here is the key information for it:

| Item                   | Value                                                                   | 
|------------------------|-------------------------------------------------------------------------|
| Process                | Django (Celery)                                                         | 
| Log files              | `/home/cstock/www/cstock/log/celery.error.log`                          |
| Configuration file      | `/home/cstock/www/cstock/code_root/logistics_project/localsettings.py` |
| View status            | `sudo supervisorctl status` (celery process)                            |
| Stop / Start / Restart | `sudo supervisorctl stop celery` (or `start`, or `restart`)             |

### Database

The database houses all persistent data for the application.
Here is the key information for it:

| Item                   | Value                                                | 
|------------------------|------------------------------------------------------|
| Process                | MySQL                                                | 
| View status            | `sudo service mysql status`                          |
| Stop / Start / Restart | `sudo service mysql stop` (or `start`, or `restart`) |

### Cache / Message Broker

The cache is used to improve the performance of the site and pass messages between other processes.
Here is the key information for it:

| Item                   | Value                                                | 
|------------------------|------------------------------------------------------|
| Process                | Redis                                                | 
| View status            | `sudo service redis status`                          |
| Stop / Start / Restart | `sudo service redis stop` (or `start`, or `restart`) |

### Web Server

The web server sits in front of the web application, providing outside internet access. It also hosts static files like images.
Here is the key information for it:

| Item                   | Value                                                | 
|------------------------|------------------------------------------------------|
| Process                | Nginx                                                | 
| Log files              | `/var/log/nginx/`                                    | 
| Configuration file     | `/etc/nginx/sites-available/cstock`                  | 
| View status            | `sudo service nginx status`                          |
| Stop / Start / Restart | `sudo service nginx stop` (or `start`, or `restart`) |


### SMS Gateway

The SMS Gateway connects to third-party SMS providers (TNM and Airtel) and routes the messages to the SMS application process.
Here is the key information for it:

| Item                   | Value                                                 | 
|------------------------|-------------------------------------------------------|
| Process                | Kannel                                                | 
| Log files              | `/var/log/kannel/`                                    | 
| Configuration file     | `/etc/kannel/kannel.conf`                             | 
| View status            | `sudo service kannel status`                          |
| Stop / Start / Restart | `sudo service kannel stop` (or `start`, or `restart`) |
