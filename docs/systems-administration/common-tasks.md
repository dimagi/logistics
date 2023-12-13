Common System Administration Tasks
==================================

These are some common tasks required of system administrators.

All of these tasks require [server access](./server-access.md).

## Deploying Updated Code

Deploying code requires installing fabric3:

```
pip install -r requrements/deploy/dev-requirements.txt
```

And then cloning [the code repository](https://github.com/dimagi/logistics/):

```
git clone https://github.com/dimagi/logistics.git
```

Then, to deploy you must first connect to the VPN. Then run the following command in the repository root:

```
fab malawi deploy
```

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

## Restarting the web server

To restart the web server you can run:

```
sudo service nginx restart
```

## Restarting the database

To restart the database you can run:

```
sudo service mysql restart
```

## Restart the SMS gateway

To restart the SMS gateway you can run:

```
sudo service kannel restart
```
