from logistics.models import SupplyPoint

from logistics_project.apps.malawi.warehouse import warehouse_view
# from logistics_project.apps.malawi.util import facility_supply_points_below,\
#     get_supervisors, get_hsa_supervisors, hsas_below, hsa_supply_points_below, get_in_charge
from logistics_project.apps.malawi.warehouse.models import UserProfileData

class View(warehouse_view.MalawiWarehouseView):

    def get_context(self, request):
        district_table = {
            "title": "",
            "id": "district_table",
            "header": ["District", "Code", "Facilities", "HSA supervisors", "HSAs", "Contacts"],
            "data": [],
        }
        facility_table = {
            "title": "",
            "id": "facility_table",
            "header": ["Facility", "Code", "GPS coordinate", "In Charge", "HSA supervisors", "Supervisor Contacts", "HSAs"],
            "data": [],
        }
        hsa_table = {
            "title": "",
            "id": "hsa_table",
            "header": ["HSA Name", "Id", "Contact Info", "Products", "Date of last message", "Last Message"],
            "data": [],
        }

        for up in UserProfileData.objects.all():
            if up.supply_point.type.code == 'd':
                district_table["data"].append([up.supply_point.name, up.supply_point.code,
                        up.facility_children, up.hsa_supervisors, up.hsa_children, up.contacts])
            elif up.supply_point.type.code == 'hf':
                gps_coord = "No Data"
                if up.supply_point.location.point:
                    if up.supply_point.location.point.latitude and up.supply_point.location.point.longitude:
                        gps_coord = "(%.2f,%.2f)" % (up.supply_point.location.point.latitude, up.supply_point.location.point.longitude)
                facility_table["data"].append([up.supply_point.name, up.supply_point.code,
                        gps_coord, up.in_charge, up.hsa_supervisors, up.supervisor_contacts,
                        up.hsa_children])
            elif up.supply_point.type.code == 'hsa':
                hsa_table["data"].append([up.supply_point.name, up.supply_point.code,
                        up.contact_info, up.products_managed,
                        up.last_message.date.strftime("%b-%d-%Y"), up.last_message.text])


        return {
                "district_table": district_table,
                "facility_table": facility_table,
                "hsa_table": hsa_table,
                }
