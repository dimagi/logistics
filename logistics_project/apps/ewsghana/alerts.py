from __future__ import absolute_import
from django.core.urlresolvers import reverse
from rapidsms.models import Contact
from alerts import Alert
from logistics.util import config
from logistics.decorators import place_in_request, return_if_place_not_set

class ConsumptionNotSet(Alert):
    # url aggregate view

    def __init__(self, supply_point ):
        self._supply_point = supply_point
        super(ConsumptionNotSet, self).__init__(self._get_text(), 
                                                reverse('aggregate', 
                                                        args=(supply_point.code, )))

    def _get_text(self):
        return "%(place)s does not have all its consumption values set." % \
                {"place": self._supply_point.name}

@place_in_request()
@return_if_place_not_set()
def consumption_not_set(request):
    facilities = request.location.all_child_facilities()
    if not facilities:
        return None
    return [ConsumptionNotSet(facility) for facility in facilities \
                              if not facility.are_consumptions_set()]

class FacilitiesWithoutInChargeAlert(Alert):
    # url is facility list view

    def __init__(self, supply_point ):
        self._supply_point = supply_point
        super(FacilitiesWithoutInChargeAlert, self)\
            .__init__(self._get_text(), 
                      reverse("facility_detail", 
                              args=(self._supply_point.code, )))

    def _get_text(self):
        return "%(place)s has no in-charge registered." % \
                {"place": self._supply_point.name}

@place_in_request()
@return_if_place_not_set()
def facilities_without_incharge(request):
    facilities = request.location.all_child_facilities()
    # totally ghana-specific
    facilities = facilities.exclude(type=config.SupplyPointCodes.CHPS)\
                                         .exclude(type=config.SupplyPointCodes.CLINIC)
    if not facilities:
        return None
    return [FacilitiesWithoutInChargeAlert(facility) for facility in facilities \
            if facility.reportees().count() == 0]
    
class ContactWithoutPhoneAlert(Alert):
    # url is contact view

    def __init__(self, contacts ):
        self._contacts = contacts
        super(ContactWithoutPhoneAlert, self).__init__(self._get_text(), 
                                                       reverse("registration_edit", 
                                                               args=(self._contacts.pk,)))

    def _get_text(self):
        return "No phone numbers associated with: %(contact)s." % \
                {"contact": self._contacts}

@place_in_request()
@return_if_place_not_set()
def contact_without_phone(request):
    facilities = request.location.all_child_facilities()
    contacts = Contact.objects.filter(is_active=True, supply_point__in=facilities).distinct()
    if not contacts:
        return None
    return [ContactWithoutPhoneAlert(contact) for contact in contacts \
            if contact.connection_set.count() == 0]

    
