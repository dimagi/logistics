import psycopg2
from psycopg2.extensions import *
import sys
# Try to connect

try:
    conn=psycopg2.connect("dbname='ilsgateway' user='postgres' password='qsczse'")
except:
    print "I am unable to connect to the database, exiting."
    sys.exit()

conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cur = conn.cursor()
try:
    cur.execute("""DROP DATABASE ilsgateway""")
except:
    print "I can't drop our test database, check your isolation level."
    sys.exit()
