from rapidsms.contrib.locations.models import LocationType
from rapidsms.models import Contact
from django.db import models
from logistics.models import ProductType, SupplyPoint
# don't remove this - it's where signals get instantiated
from logistics_project.apps.ewsghana import signals
from logistics.util import config

class EscalatingAlertRecipients(models.Model):
    """ who should receive escalating alerts? 
    all district users? regional users of a certain program? etc.
    this is used in the custom notifications.py alerts"""
    location_type = models.ForeignKey(LocationType)
    program = models.ForeignKey(ProductType, blank=True, null=True)

    def __unicode__(self):
        if self.program:
            return "%s - %s" % (self.location_type.name, self.program.name)
        return self.location_type.name
    
class GhanaFacility(SupplyPoint):
    class Meta:
        proxy = True

    def get_district_incharges(self):
        """ ghana wants it so that the in-charge of facility in the surrounding region
        can be designated the in-charge of a given facility
        (this is to support the use case of CHWs who report to a local health center in-charge)
        """
        supervise_resp = config.Responsibilities.REPORTEE_RESPONSIBILITY
        supervisors = Contact.objects.filter(role__responsibilities__code=supervise_resp)
        supervisors = supervisors.order_by("supply_point__name")
        district = self.location
        while district.type and district.tree_parent and district.type.slug != config.LocationCodes.DISTRICT:
            district = district.tree_parent 
        return supervisors.filter(supply_point__location__in=district.get_descendants(include_self=True), supply_point__active=True)
