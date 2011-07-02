import pyodbc
import decimal # needed for py2exe/pyodbc
import logging
import logging.handlers
from datetime import datetime, date, timedelta
import json
import urllib2, urllib
import os
import os.path
import httplib
import smtplib
import time
from email.mime.text import MIMEText
from socket import gaierror

# Why is this all hardcoded, you might ask?  I want the email_log function to succeed
# if there's any error in the config, and that means hardcoding these parameters.
# They shouldn't change, anyway.

LOG_PATH="scmgr.log"
CONFIG_PATH="config.txt"
DB_CONFIG_PATH="db.txt" # We use a separate config file for the DB path,
                        # since we know this setting has to change.
                        # It also makes it easier to not have to escape backslashes.
EMAIL_HOST="smtp.gmail.com"
EMAIL_PORT=587
EMAIL_HOST_USER="logistics-support@dimagi.com"
EMAIL_HOST_PASSWORD="replace this with password"
EMAIL_USE_TLS=True
EMAIL_DESTINATION="cternus@dimagi.com"

def email_log(subject):
    try:
        fp = open(log.handlers[0].baseFilename, 'rb')
        msg = MIMEText(fp.read())
        fp.close()
        msg['Subject'] = subject
        msg['From'] = EMAIL_HOST_USER
        msg['To'] = EMAIL_DESTINATION
        server = smtplib.SMTP(EMAIL_HOST)
        server.starttls()
        server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
        server.sendmail(EMAIL_HOST_USER, EMAIL_DESTINATION, msg.as_string())
    except gaierror:
        print "\n\n************!!!!!!!!!!!!!!!**************"
        print "Couldn't email the log!  Are you sure you're connected to the Internet?"
        print "Close this window and try again in a few minutes, or email this file:"
        print log.handlers[0].baseFilename
        print "to logistics-support@dimagi.com if it still doesn't work."
        print "Once you've done so, you can close this window."
        time.sleep(-1)
    except Exception as e:
        print "\n\n************!!!!!!!!!!!!!!!**************"
        log.exception("Couldn't email the log.  Something went wrong!")
        print "Send a copy of the file"
        print log.handlers[0].baseFilename
        print "to logistics-support@dimagi.com and tell them about this error."
        print "Once you've done so, you can close this window."
        time.sleep(-1) # wait forever
    
def init_logging ():
    """initialize the logging framework"""
    global log
    log = logging.getLogger('extract')
    log.setLevel(logging.DEBUG)
    handler = logging.handlers.RotatingFileHandler(LOG_PATH, maxBytes=524288, backupCount=2)
    formatter = logging.Formatter("%(asctime)s;%(levelname)s;%(message)s")
    handler.setFormatter(formatter)
    log.addHandler(handler)
    log.addHandler(logging.StreamHandler())

if __name__=='__main__':
    cwd = os.path.abspath(os.path.curdir)
    init_logging()
    try:
        f = open(CONFIG_PATH, "r")
        config = json.load(f)
        f.close()
        log.info("Finding database...")
        dbpf = open(DB_CONFIG_PATH, "r")
        dbp = dbpf.readline().strip()
        if not os.path.isfile(dbp):
            log.error("Couldn't find the database!")
            log.error("Looked for it at %s, but it wasn't there." % dbp)
            log.error("Are you sure the path in %s is correct?" % os.path.abspath(DB_CONFIG_PATH))
            log.error("Check it, close this window, and try again.")
            email_log("SCMgr Database Not Found")
            time.sleep(-1)            
        log.info("Connecting to database...")
        cnxn = pyodbc.connect('DRIVER={Microsoft Access Driver (*.mdb)};DBQ=%s' % dbp)        
        c = cnxn.cursor()
        log.info("Connecting to cStock...")
        h = httplib.HTTPConnection(config['SUBMIT_HOST'])
        h.connect()
        h.close()# We close this connection again, otherwise it will time out.        
        log.info("Fetching data from SCMgr (this may take a few minutes)...")
        c.execute(config['QUERY'])
        log.info("Sending data to cStock...")
        h = httplib.HTTPConnection(config['SUBMIT_HOST'])
        while True:
            res = c.fetchmany(config['CHUNK_SIZE'])
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
            h.request('POST', config['SUBMIT_URL'], params, headers)
            response = h.getresponse()
            if response.status == 201:
                log.info(response.read())
                continue
            elif response.status == 200:
                log.info(response.read())
                break
            else:
                log.error(response.status)
                log.error(response.reason)
                log.error(response.msg)
                break
        log.info("Sending log information...")
        email_log("SCMgr Update Success")
        log.info("Congratulations, cStock has been fully updated. You may close this window now.")
    except gaierror:
        log.error("Couldn't connect to the network!  Are you sure you're connected to the Internet?")
        log.error("Close this window and try again.")
    except Exception as e:
        log.exception("Something went wrong!")
        log.error(config)
        log.error("Telling the engineers about the problem...")
        email_log("SCMGR Error")
        log.error("Done.  You may close this window now.")
    time.sleep(-1)
        
