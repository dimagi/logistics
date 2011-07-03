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
import urllib2, urllib
from urlparse import urlparse
from threading import Thread
import os
import os.path
import bz2
import httplib

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

def dbconn():
    """return a database connected to the production (ZPCT access) or staging (UNICEF sqlite) databases"""
    return pyodbc.connect('DRIVER={Microsoft Access Driver (*.mdb)};DBQ=%s' % config.PRODUCTION_DB_PATH)


if __name__=='__main__':
    print "Connecting to database..."
    cnxn = dbconn()
    c = cnxn.cursor()
    print "Connecting to cStock..."
    h = httplib.HTTPConnection(config.SUBMIT_HOST)
    print "Executing query..."
    c.execute(config.QUERY)
    print "Transmitting data:"
    while True:
        res = c.fetchmany(config.CHUNK_SIZE)
        if not res:
            break
        data = []
        for r in res:
            r[4] = [r[4].year, r[4].month]
            data.append(list(r))
        val = {"data": json.dumps(data)}
        params = urllib.urlencode(val)
        headers = {"Content-type": "application/x-www-form-urlencoded",
                   "Accept": "text/plain"}
        h.request('POST', config.SUBMIT_URL, params, headers)
        response = h.getresponse()
        if response.status == 201:
            print response.read()
            continue
        else:
            print response.reason, response.read()
            break
    print "All data transmitted."
