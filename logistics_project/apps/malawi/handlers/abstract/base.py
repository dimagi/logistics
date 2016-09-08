from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from logistics.util import config


class RecordResponseHandler(KeywordHandler):
    """
    Record when you make a response
    """
    _responded = False
    
    def respond(self, template, **kwargs):
        super(RecordResponseHandler, self).respond(template, **kwargs)
        self._responded = True
    
    
    @property
    def responded(self):
        return self._responded


class FacilityUserHandler(KeywordHandler):
    """
    Intended to be used when Facility users need to interact with the system
    over SMS.
    """

    def validate_contact(self):
        """
        Checks if the contact who sent this message can use the keyword
        and returns that contact's supply point if so.
        """
        contact = getattr(self.msg,'logistics_contact', None)
        if contact and contact.is_active:
            supply_point = contact.supply_point
            if supply_point and supply_point.type.code == config.SupplyPointCodes.FACILITY:
                return supply_point

        return None
