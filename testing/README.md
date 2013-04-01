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

Better documentation coming soon.

Load Testing the Reports
------------------------

We setup some basic [selenium](http://docs.seleniumhq.org/) tests to login to the site and hit the reports.
You can use a tool like [Neustar Web Performance](http://www.neustar.biz/enterprise/web-performance) to turn
this into a load test. For details on how to do this (which require creating an account) please see the Neustar
web page.

