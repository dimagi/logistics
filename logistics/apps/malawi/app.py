from logistics.apps.logistics.app import App as LogisticsApp, SOH_KEYWORD
from logistics.apps.logistics.models import ProductReportsHelper,\
    StockRequest, ContactRole
from django.conf import settings
from django.db import transaction
from logistics.apps.malawi import const
from rapidsms.models import Contact
from logistics.apps.malawi.const import Messages
from logistics.apps.logistics.const import Reports

class App(LogisticsApp):
    """
    Once upon a time this app overrode some stuff.
    All logic has since been moved into handlers, 
    and this actually does nothing.
    """
    
    def start (self):
        # don't do all the scheduling stuff
        pass
    
    def handle (self, message):
        pass
        
    def default(self, message):
        # the base class overrides all possible responses. 
        # this avoids that problem.
        pass
    
    