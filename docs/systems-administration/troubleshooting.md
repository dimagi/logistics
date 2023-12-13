Troubleshooting
===============

Some common issues, and how to resolve them.

## Monitoring

The project uses [Sentry](https://sentry.io/) for error monitoring.
Whenever there is an error in the application it will be logged to Sentry, and an alert will be sent to all Sentry users.

## Common errors

Some common error messages from Sentry are documented here.

### "Too many connections" error

If you see errors in Sentry saying "too many connections", it is an issue with too many open connections to the
MySQL database.

Typically, these connections are caused by database connections left open by the rapidsms router process.
Restarting the router process usually resolves this:

```
sudo supervisorctl restart rapidsms-router
```

### "Warehouse already running, will do nothing..."

This error indicates that a background job that builds the cStock reports every 12 hours failed because
the previous one has not completed.

1. If it is the first time you have seen the error in a while, check if it is the first of the month. If it is, you can likely ignore it. The warehouse job takes longer than usual on the first and this is expected.
2. If it is not the first, or you see the error multiple times in a row you should check the warehouse runner status (see the deploy section above).
3. By looking in the logs, if the job is still running you can ignore it.
4. If the job has died, you should manually go to the admin page and set the status of the most recent job to "complete". Unintuitively you should also set "has_error" to False, despite the fact that the job likely errored. This is due to a legacy issue with how that field is used.

## SMS issues

The first place to check for troubleshooting SMS issues is the [SMS status page](https://cstock.health.gov.mw/malawi/status/) on the site.

The following is an example output from that page:

```
    Kannel bearerbox version `1.4.5'.
Compiler `11.2.0'.
System Linux, release 5.15.0-88-generic, version #98-Ubuntu SMP Mon Oct 2 15:18:56 UTC 2023, machine x86_64.
Hostname cstock, IP 127.0.1.1.
Libxml version 2.9.12.
Using OpenSSL 3.0.0 7 sep 2021.
Compiled with MySQL 8.0.27, using MySQL 8.0.35.
Compiled with PostgreSQL 14.1 (Ubuntu 14.1-1ubuntu1).
Using SQLite 3.36.0.
Using hiredis API 0.14.1
Using native malloc.


Status: running, uptime 32d 22h 13m 28s

WDP: received 0 (0 queued), sent 0 (0 queued)

SMS: received 4461 (0 queued), sent 9185 (1178 queued), store size -1
SMS: inbound (0.02,0.00,0.00) msg/sec, outbound (0.12,0.03,0.00) msg/sec

DLR: received 0, sent 0
DLR: inbound (0.00,0.00,0.00) msg/sec, outbound (0.00,0.00,0.00) msg/sec
DLR: 0 queued, using internal storage

Box connections:
    smsbox:(none), IP 127.0.0.1 (0 queued), (on-line 32d 22h 13m 27s)  


SMSC connections:
    airtel-smpp[airtel-smpp]    SMPP:messaging.airtel.mw:9001/9001:mnofhlth:VMA (online 178261s, rcvd: sms 2579 (0.02,0.00,0.00) / dlr 0 (0.00,0.00,0.00), sent: sms 5573 (0.12,0.03,0.00) / dlr 0 (0.00,0.00,0.00), failed 0, queued 0 msgs)
    tnm-smpp-send[tnm-smpp-send]    SMPP:41.78.250.95:5016/5016:CStock:SMPP (re-connecting, rcvd: sms 0 (0.00,0.00,0.00) / dlr 0 (0.00,0.00,0.00), sent: sms 3612 (0.00,0.00,0.00) / dlr 0 (0.00,0.00,0.00), failed 8, queued 0 msgs)
    tnm-smpp-receive-1[tnm-smpp-receive-1]    SMPP:41.78.250.40:5019/5019:CStock:SMPP (online 178174s, rcvd: sms 1882 (0.03,0.01,0.00) / dlr 0 (0.00,0.00,0.00), sent: sms 0 (0.00,0.00,0.00) / dlr 0 (0.00,0.00,0.00), failed 0, queued 0 msgs)
    tnm-smpp-receive-2[tnm-smpp-receive-2]    SMPP:41.78.250.42:5019/5019:CStock:SMPP (re-connecting, rcvd: sms 0 (0.00,0.00,0.00) / dlr 0 (0.00,0.00,0.00), sent: sms 0 (0.00,0.00,0.00) / dlr 0 (0.00,0.00,0.00), failed 0, queued 0 msgs)




Last Celery Heartbeat:2023-12-13 16:17:00.029043
```

The most important part is the bottom section, labeled `SMSC connections`.
This will show the status of the four connections to SMS gateways (one for airtel, and 3 for TNM).
If the connection reports `online` then it is working as expected.
If it says `re-connecting` or anything else, it is not working.

The most common reason that SMS fails is due to VPN issues between cStock and TNM.
These need to be resolved by the cStock hosting team and TNM networking team.
