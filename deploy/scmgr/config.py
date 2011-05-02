import os
VERSION = '0.0.1'

BASE_PATH = os.path.abspath(os.path.dirname(__file__))
STAGING_DB_NAME = "scmgr.db"
STAGING_DB_PATH = os.path.join(BASE_PATH, STAGING_DB_NAME)
LOG_PATH = os.path.join(BASE_PATH, 'extract.log')
LOG_TO_CONSOLE = True

# path to the SCMgr database
PRODUCTION_DB_PATH = r'C:\Users\czue\source\scmgr\Malawi_Central_Master_live.mdb'                                        

# RapidSMS server to submit to
SUBMIT_URL = 'http://localhost:8000/scmrg/incoming/'    


# from here below is currentlly unused.
"""



auth_params = dict(realm='Lab Results', user='adh', passwd='aibieV9ree')

always_on_connection = False       #if True, assume computer 'just has' internet



transport_chunk = 5000  #maximum size per POST to rapidsms server (bytes) (approximate)
send_compressed = False  #if True, payloads will be sent bz2-compressed
compression_factor = .2 #estimated compression factor


#wait times if exception during db access (minutes)
db_access_retries = [2, 3, 5, 5, 10]

#wait times if error during http send (seconds)
send_retries = [0, 0, 0, 30, 30, 30, 60, 120, 300, 300]

source_tag = 'ndola/arthur-davison'

daemon_lock = base_path + 'daemon.lock'
task_lock = base_path + 'task.lock'
"""