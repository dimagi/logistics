Common System Administration Tasks
==================================

## Deploying Code

To deploy code you must first connect to the VPN. Then run:

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
