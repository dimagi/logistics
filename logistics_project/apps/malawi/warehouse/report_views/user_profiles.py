from __future__ import unicode_literals
from logistics.models import SupplyPoint
from logistics.util import config

from logistics_project.apps.malawi.warehouse import warehouse_view
from logistics_project.apps.malawi.warehouse.report_utils import get_hsa_url
from logistics_project.apps.malawi.util import get_default_supply_point,\
    get_district_supply_points, get_imci_coordinators,\
    facility_supply_points_below, get_in_charge, hsa_supply_points_below,\
    get_supervisors

class View(warehouse_view.DistrictOnlyView):

    def custom_context(self, request):

        district = SupplyPoint.objects.none()
        facility = SupplyPoint.objects.none()

        # set district or facility based on user
        sp = SupplyPoint.objects.get(location=request.location)\
            if request.location else get_default_supply_point(request.user)

        if sp.type.code == config.SupplyPointCodes.DISTRICT:
            district = sp
        elif sp.type.code == config.SupplyPointCodes.FACILITY:
            facility = sp

        # override default with queried district or facility
        if request.GET.get('district'):
            district = SupplyPoint.objects.get(code=request.GET.get('district'))
        if request.GET.get('facility'):
            facility = SupplyPoint.objects.get(code=request.GET.get('facility'))

        # helpers
        def _names_and_numbers(contacts):
            return [
                ", ".join(c.name for c in contacts),
                ", ".join(c.default_connection.identity or "none" for c in contacts),
            ] if contacts else ["none set", "n/a"]
        
        def _gps_coord(supply_point):
            point = supply_point.location.point
            return "(%.2f,%.2f)" % (point.latitude, point.longitude) \
                if (point and point.latitude and point.longitude) else "No Data"
                            
        district_data = []
        for sp in get_district_supply_points():
            district_data.append({
                "url": _get_url(sp),
                "data": [
                    sp.name,
                    sp.code,
                    facility_supply_points_below(sp.location).count(),
                    hsa_supply_points_below(sp.location).count(),
                ] + _names_and_numbers(get_imci_coordinators(sp))
            })
        
        district_table = {
            "id": "district_table",
            "is_datatable": True,
            "is_downloadable": True,
            "header": ["District", "Code", "# facilities", "# HSAs", "District IMCI coordinator", "Contact"],
            "data": district_data
        }
        
        facility_table = None
        if district:
            facility_data = []
            for sp in facility_supply_points_below(district.location):
                facility_data.append({
                    "url": _get_url(sp),
                    "data": [sp.name, sp.code, _gps_coord(sp), hsa_supply_points_below(sp.location).count()] +
                            _names_and_numbers(get_in_charge(sp))
                })
            facility_table = {
                "id": "facility_table",
                "is_datatable": True,
                "is_downloadable": True,
                "header": ["Facility", "Code", "GPS coordinate", "# HSAs", "HF in charge", "Contact"],
                "data": facility_data
            }
            
        hsa_table = None
        if facility:
            hsa_data = []
            for sp in hsa_supply_points_below(facility.location):
                hsa_data.append({"url": get_hsa_url(sp),
                                 "data": [sp.name, sp.code, 
                                          sp.contacts()[0].default_connection.identity] + \
                                         _names_and_numbers(get_supervisors(sp.supplied_by))})

            hsa_table = {
                "id": "hsa_table",
                "is_datatable": True,
                "is_downloadable": True,
                "header": ["HSA Name", "Id", "Contact", "Supervisor", "Contact"],
                "data": hsa_data,
            }

        return {
                "district": district,
                "facility": facility,
                "district_table": district_table,
                "facility_table": facility_table,
                "hsa_table": hsa_table,
        }

def _get_url(supply_point):
    querystring = 'district=%s' % supply_point.code\
        if supply_point.type.code == 'd' else 'district=%s&facility=%s' % (supply_point.supplied_by.code, supply_point.code)
    return '/malawi/r/user-profiles/?%s' % querystring

