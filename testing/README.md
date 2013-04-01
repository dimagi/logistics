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

