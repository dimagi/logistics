Load testing for the Malawi project
===================================

Here's the basic steps to load test:

1. Setup a demo environment with the cStock code and data deployed (see the project readme for more information)
2. Use the `multiply_data` management command to multiply the data set to your preferred size
3. Run the tests

Creating the environment
------------------------

First setup a development environment by following the instructions in the project readme. Then get a database
up and running with the some data by using a tool like mysqldump or pgdump on a real (or demo) data set.

If you are going to be conducting the SMS load testing you should add a load testing backend to the
`INSTALLED_BACKENDS` property of your `localsettings.py` file. The configuration for this backend should
look something like this:

    INSTALLED_BACKENDS = {
        # other backends go here...
        'loadtest': {
            "ENGINE":  "rapidsms.backends.http",
            "port": 9988,
            "gateway_url": "http://www.example.com",
            "params_outgoing": "id=%(phone_number)s&text=%(message)s",
            "params_incoming": "id=%(phone_number)s&text=%(message)s"
        },
    }


Generating Data
---------------

Once the environment is setup with data you can use a management command to multiply all of the HSAs in the system.
This will duplicate all of the HSAs any number of times, and include all of their historical stock data which will
show up in all reports. To run this command just enter:

    python manage.py multiply_data [number]

where `[number]` is the multiplier.

Load Testing the SMS
--------------------

We setup a basic SMS load test using [multi-mechanize](http://testutils.org/multi-mechanize/) to allow for the
simulation of any number of SMS stock messages coming in at the same time.

There are a few steps to setup SMS load testing.

### Install multimechanise

Follow [these instructions](http://testutils.org/multi-mechanize/setup.html) for your platform.

### Configure scripts

Edit the `config.cfg` file in the `cstock_sms_test` directory according to the number of concurrent messages you
want to test and any other settings.

Edit the `test_scripts/test_sms` file in the same directory and set the `BACKEND_URL` parameter to your server's
address and port of the loadtest backend that you configured.

### Run scripts

    ./multimech-run cstock_sms_test

The results will show up in the `cstock_sms_test` directory.


Load Testing the Reports
------------------------

It should be very easy to use existing tools / macros to setup some basic [selenium](http://docs.seleniumhq.org/)
tests to login to the site and hit the reports. For creating scripts we recommend using Mozilla Firefox and
[Selenium IDE](http://docs.seleniumhq.org/docs/02_selenium_ide.jsp).

You can use a tool like [Neustar Web Performance](http://www.neustar.biz/enterprise/web-performance/what-is-load-testing)
to turn this into a load test. For details on how to do this (which require creating an account) please see the
Neustar web page.
