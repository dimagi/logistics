Common System Administration Tasks
==================================

## Deploying Code

Deploying code requires installing fabric3 (`pip install -r requrements/deploy/dev-requirements.txt`).

Then, to deploy you must first connect to the VPN. Then run:

```
fab malawi deploy
```

## Restarting processes

We use supervisor (`/etc/supervisor.conf`) to manage the running processes.

To see the list of running processes run:

```
sudo supervisorctl status
```

You can restart individual processes with:

```
sudo supervisorctl restart <process-name>
```
