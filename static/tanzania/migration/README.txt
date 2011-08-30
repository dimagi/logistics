These are the migration files for ILSGateway.

Migration process:

1. Start with a cleaned database (have to manually clean out test data).
2. pg_dump / restore to new temporary migration database
   > pg_dump [cleaneddatabase] > [dumpfile].sql
   > psql [migrationdatabase] < [dumpfile].sql
3. Connect to temporary migration and run migration queries in the queries folder. 
   > psql [migrationdatbase]
   > (paste individual queries here)
   - You may need to modify paths to get them to work
4. Copy export files to this folder
5. (If not done, create production database)
   > createdb logistics
   > ./manage.py syncdb
   > ./manage.py migrate
6. Start router 
   > ./manage.py runrouter
7. Run migration
   > ./manage.py tz_migrate
   
Post Migration:

1. Change the localsettings backend from "push" to "push_backend" to reactivate everyone's real backends.
2. Make sure the default connection is "push_backend". This must supercede the migration backend. 
 