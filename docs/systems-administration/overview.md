cStock System Overview
======================

[cStock](https://cstock.health.gov.mw/) is a website built and maintained by the Malawi Ministry of Health.
There is a web component as well as an SMS component.

## Hosting

cStock is hosted by the Ministry of Health.

## Code

The cStock application code is hosted [on Github](https://github.com/dimagi/logistics/).
It is a Python / Django application, based on RapidSMS.

In general system administrators should not need to modify cStock code,
but it would be necessary to add new features or fix bugs.

## Key Services

cStock consists of the following key services:

| Service                 | Description                                                                                                                      | Technology        |
|-------------------------|----------------------------------------------------------------------------------------------------------------------------------|-------------------|
| Web Application Process | The web application is the business logic that powers the cStock web application.                                                | Django            |
| SMS Application Process | A process that runs alongside the web application to manage SMS workflows                                                        | Django + RapidSMS |
| Background Task Process | A process that runs alongside the web application to manage background tasks and scheduled SMS messages                          | Django + Celery   |
| Database                | The database houses all persistent data.                                                                                         | MySQL             |
| Web Server              | The web server sits in front of the web application, providing outside internet access. It also hosts static files like images.  | Nginx             |
| SMS Gateway             | The SMS Gateway connects to third-party SMS providers (TNM and Airtel) and routes the messages to the SMS application process.   | Kannel            |


