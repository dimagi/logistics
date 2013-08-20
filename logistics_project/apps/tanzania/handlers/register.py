from django.utils.translation import ugettext_noop as _
from rapidsms.models import Contact
from logistics.models import ContactRole, SupplyPoint
from logistics.util import config
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.contrib.handlers.handlers.tagging import TaggingHandler
import re

DISTRICT_PREFIXES = ['d', 'm', 'tb', 'tg', 'dm', 'mz', 'mt', 'mb', 'ir', 'tb', 'ms']

class ILSRegistrationHandler(KeywordHandler,TaggingHandler):
    """
    Registration for ILS Gateway
    """

    keyword = "register|reg|join|sajili"
    
    def help(self):
        self.respond(_(config.Messages.REGISTER_HELP))
    
        
    def handle(self, text):

        sp_name = None
        msd_code = None
        if text.find(config.DISTRICT_REG_DELIMITER) != -1:
            phrases = [x.strip() for x in text.split(":")]
            if len(phrases) != 2:
                self.respond_error(_(config.Messages.REGISTER_HELP))
                return True
            name = phrases[0]
            sp_name = phrases[1]

            def _respond_error(sp_name):
                kwargs = {'name': sp_name}
                self.respond_error(_(config.Messages.REGISTER_UNKNOWN_DISTRICT), **kwargs)
                return True
            try:
                sdp = SupplyPoint.objects.get(type__code="district", name__istartswith=sp_name)
            except SupplyPoint.DoesNotExist:
                return _respond_error(sp_name)
            except SupplyPoint.MultipleObjectsReturned:
                try:
                    sdp = SupplyPoint.objects.get(type__code="district", name__iexact=sp_name)
                except (SupplyPoint.DoesNotExist, SupplyPoint.MultipleObjectsReturned):
                    return _respond_error(sp_name)

        else:
            words = text.split()
            names = []
            msd_codes = []
            location_regex = '^({prefs})\d+'.format(prefs='|'.join(p.lower() for p in DISTRICT_PREFIXES))
            for the_string in words:
                if re.match(location_regex, the_string.strip().lower()):
                    msd_codes.append(the_string.strip().lower())
                else:
                    names.append(the_string)

            name = " ".join(names)

            if len(msd_codes) != 1:
                self.respond_error(_(config.Messages.REGISTER_HELP))
                return True
            else:
                [msd_code] = msd_codes
                try:
                    sdp = SupplyPoint.objects.get(code__iexact=msd_code)
                except SupplyPoint.DoesNotExist:
                    kwargs = {'msd_code': msd_code}
                    self.respond_error(_(config.Messages.REGISTER_UNKNOWN_CODE), **kwargs )
                    return True
        
        # Default to Facility in-charge or District Pharmacist for now
        if sdp.type.code.lower() == config.SupplyPointCodes.DISTRICT:
            role = ContactRole.objects.get(code__iexact=config.Roles.DISTRICT_PHARMACIST)
        elif sdp.type.code.lower() == config.SupplyPointCodes.FACILITY:
            role = ContactRole.objects.get(code__iexact=config.Roles.IN_CHARGE)
        else:
            # TODO be graceful
            self.add_tag("Error")
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

        if sp_name:
            kwargs = {'sdp_name': sdp.name,
                      'contact_name': contact.name}
            self.respond(_(config.Messages.REGISTRATION_CONFIRM_DISTRICT), **kwargs)
        else:
            kwargs = {'sdp_name': sdp.name,
                      'msd_code': msd_code,
                      'contact_name': contact.name}

            self.respond(_(config.Messages.REGISTRATION_CONFIRM), **kwargs)
