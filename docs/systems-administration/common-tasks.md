Common System Administration Tasks
==================================

These are some common tasks required of system administrators.

All of these tasks require [server access](./server-access.md).

## Deploying Updated Code

Deploying code requires installing fabric:

```
pip install -r requrements/deploy/dev-requirements.txt
```

And then cloning [the code repository](https://github.com/dimagi/logistics/):

```
git clone https://github.com/dimagi/logistics.git
```

Then, to deploy you must first connect to the VPN. Then run the following command in the repository root:

```
fab -H cstock@10.10.100.77 deploy --prompt-for-sudo-password
```

You'll need to enter the password for the cstock user on the server.

This command should be run on *your own machine*.
For the remaining sections, you must run the commands *on the server*.

## Restarting application processes

We use supervisor (`/etc/supervisor.conf`) to manage the running cStock processes,
including the web application, SMS application, and background task application.

To see the list of running processes run:

```
sudo supervisorctl status
```

You can restart individual processes with:

```
sudo supervisorctl restart <process-name>
```

## Restarting other processes

Sometimes other processes (the web server, database, etc.) need to be restarted.
To manage those you can find the information in the [overview page](./overview).

## Making configuration changes

If you need to make any configuration changes, for example, updating passwords or IP addresses,
those happen in the relevant configuration files for whichever service you need to update.

To find the service's configuration file, look it up on the [overview page](./overview).

For example, to update the credentials for the TNM or Airtel SMS gateway, you would modify
the SMS gateway (Kannel) configuration file at `/etc/kannel/kannel.conf`.

Typically, whenever you make changes to a service, you also need to restart the service,
as per the instructions above.

## Getting an application shell

Sometimes it can be useful to get an application shell, to run the cStock Python code manually,
for example, to inspect data models or make once-off changes.

To get an application shell you can enter the virtual environment like this (as the `cstock` user):

```
workon cstock
```

This should enter the virtual environment and load you in the right directory.
From there you can run:

```
python manage.py shell
```

To get a Python shell. You can then run code to work with the Django application.
For example, to see how many registered web users there are, you can run:

```
>>> from django.contrib.auth.models import User
>>> User.objects.count()
551
```

## Getting a database shell

The easiest way to get a database shell is to first enter the virtual environment as per above:

```
workon cstock
```

Then run:

```
python manage.py dbshell
```

Then to run the equivalent command in MySQL you could run:

```
mysql> SELECT count(*) FROM auth_user;
+----------+
| count(*) |
+----------+
|      551 |
+----------+
1 row in set (0.00 sec)
```
