from rapidsms.models import Contact
from logistics.models import SupplyPoint
from logistics.util import config
# don't remove this - it's where signals get instantiated
from logistics_project.apps.ewsghana import signals

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
        return supervisors.filter(supply_point__location__in=district.get_descendants(include_self=True))    
