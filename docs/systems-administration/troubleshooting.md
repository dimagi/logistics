Troubleshooting
===============

Some common issues, and how to resolve them.

# "Too many connections" error

If you see errors in Sentry saying "too many connections", it is an issue with too many open connections to the
MySQL database.

Typically, these connections are caused by database connections left open by the rapidsms router process.
Restarting the router process usually resolves this:

```
sudo supervisorctl restart rapidsms-router
```
