from django.utils.translation import ugettext as _
from logistics import settings
from rapidsms.models import Contact
from logistics.apps.logistics.models import ContactRole, SupplyPoint
from logistics.apps.malawi.handlers.abstract.register import RegistrationBaseHandler
from rapidsms.contrib.locations.models import Location
from logistics.apps.malawi.exceptions import IdFormatException
from logistics.apps.logistics.util import config
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
import re

class ILSRegistrationHandler(KeywordHandler):
    """
    Registration for ILS Gateway
    """

    keyword = "register|reg|join|sajili"
    
    def help(self):
        self.respond(config.Messages.REGISTER_HELP)
    
        
    def handle(self, text):        
        words = text.split()
        names = []
        msd_codes = []
        for the_string in words:
            if re.match('^d\d+', the_string.strip().lower()):
                msd_codes.append(the_string.strip().lower())
            else:
                names.append(the_string)
        
        name = " ".join(names) 
        
        if len(msd_codes) != 1:
            self.respond(_(config.Messages.REGISTER_BAD_CODE))
            return True
        else:
            [msd_code] = msd_codes
            try:
                sdp = SupplyPoint.objects.get(code__iexact=msd_code)
            except SupplyPoint.DoesNotExist:
                kwargs = {'msd_code': msd_code}
                self.respond(_(config.Messages.REGISTER_UNKNOWN_CODE), **kwargs )
                return True
        
        # Default to Facility in-charge or District Pharmacist for now
        if sdp.type.code.lower() == config.SupplyPointCodes.DISTRICT:
            role = ContactRole.objects.get(code__iexact=config.Roles.DISTRICT_PHARMACIST)
        elif sdp.type.code.lower() == config.SupplyPointCodes.FACILITY:
            role = ContactRole.objects.get(code__iexact=config.Roles.IN_CHARGE)
        else:
            # TODO be graceful
            raise Exception("bad location type: %s" % sdp.type.name)
            
        contact = self.msg.logistics_contact if hasattr(self.msg,'logistics_contact') else Contact()
        contact.name = name
        contact.supply_point = sdp
        contact.role = role
        contact.is_active = True
        contact.is_approved = True
        contact.language = config.Languages.DEFAULT
        contact.save()
        
        self.msg.connection.contact = contact
        self.msg.connection.save()

        kwargs = {'sdp_name': sdp.name,
                  'msd_code': msd_code,
                  'contact_name': contact.name}

        self.respond(_(config.Messages.REGISTRATION_CONFIRM), **kwargs)
