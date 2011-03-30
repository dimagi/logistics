import pyodbc
import sqlite3
import config
import logging
import logging.handlers
from datetime import datetime, date, timedelta
from datetime import time as timeofday
import time
import re
import random
import json
import urllib2
from urlparse import urlparse
from threading import Thread
import os
import os.path
import bz2

identity = lambda x: x

def init_logging ():
    """initialize the logging framework"""
    global log
    log = logging.getLogger('extract')
    log.setLevel(logging.DEBUG)
    handler = logging.handlers.RotatingFileHandler(config.LOG_PATH, maxBytes=1048576, backupCount=2)
    formatter = logging.Formatter("%(asctime)s;%(levelname)s;%(message)s")
    handler.setFormatter(formatter)
    log.addHandler(handler)
    if config.LOG_TO_CONSOLE:
        log.addHandler(logging.StreamHandler())

def dbconn (db):
    """return a database connected to the production (ZPCT access) or staging (UNICEF sqlite) databases"""
    if db == 'prod':
        return pyodbc.connect('DRIVER={Microsoft Access Driver (*.mdb)};DBQ=%s' % config.PRODUCTION_DB_PATH)
    elif db == 'staging':
        return sqlite3.connect(config.STAGING_DB_PATH, 
                               detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    else:
        raise ValueError('do not recognize database [%s]' % db)

def hello_world():
    """Tests the production database connection"""
    conn = dbconn('prod')
    curs = conn.cursor()
    sql = "SELECT top 1 * from CTF_Item;"
    curs.execute(sql)
    for rec in curs.fetchall():
        log.info('got record: %s' % rec)
    curs.close()
    conn.close()
  

def pkey_fetch (curs, query, args=()):
    """query the primary key column of a table and return the results as a set of ids"""
    curs.execute(query, args)
    return set(rec[0] for rec in curs.fetchall())

def init_staging_db (lookback):
    """initialize the staging database"""
    create_staging_db()
    log.info('staging db initialized')
    
def create_staging_db ():
    """create the tables in the sqlite db"""
    conn = dbconn('staging')
    curs = conn.cursor()
    curs.execute('''
      create table samples (
        sample_id varchar(10) primary key,  --id assigned to sample in lab
        imported_on date,                   --when sample record was discovered by extract script
        resolved_on date,                   --when result was noticed by extract script
        patient_id varchar(100),            --patient 'identifier' from requisition form
        facility_code int,
        collected_on date,                  --date sample was collected at clinic
        received_on date,                   --date sample was received at/entered into lab system
        processed_on date,                  --date sample was tested in lab
        result varchar(20),                 --result: 'positive', 'negative', 'rejected', 'indeterminate', 'inconsistent'
        result_detail varchar(100),         --e.g., reason rejected
        birthdate date,
        child_age int,                      --in months (may be inconsistent with birthdate)
        health_worker varchar(50),          --name of clinic worker collecting sample
        health_worker_title varchar(50),    --title of clinic worker
        sync_status varchar(10) not null default 'new'  --status of record's sync with rapidsms server: 'new', 'updated',
                                                        --'synced', 'historical'
      )
    ''')
      
    conn.commit()
    curs.close()
    conn.close()

FAIL_MSG = """
===========================================================================
                            EXPORT FAILED!!!
===========================================================================
Review the log file at %s for more information.
 
Press ENTER to continue""" % (config.LOG_PATH)

SUCCESS_MSG = """
===========================================================================
                                SUCCESS
===========================================================================

Press ENTER to continue""" 

if __name__ == "__main__":
    try:
        print "starting"
        init_logging()
        hello_world()
        raise(Exception("fail"))
        print SUCCESS_MSG
        raw_input()
    except Exception, e:
        logging.exception(e)
        print FAIL_MSG 
        raw_input()
