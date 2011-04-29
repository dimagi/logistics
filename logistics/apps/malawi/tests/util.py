from logistics.apps.malawi.const import Messages
from logistics.apps.logistics.models import SupplyPoint, ContactRole,\
    StockRequest
from rapidsms.models import Contact


def create_hsa(test_class, phone, name, id="1", facility_code="2616"):
    a = """
           %(phone)s > register %(name)s %(id)s %(code)s
           %(phone)s < %(confirm)s
        """ % {"phone": phone, "name": name, "id": id, "code": facility_code,
               "confirm": Messages.REGISTRATION_CONFIRM % \
                    {"sp_name": SupplyPoint.objects.get(code=facility_code).name,
                     "role": "hsa",
                     "contact_name": name}}
    test_class.runScript(a)
    return Contact.objects.get(name=name)

def create_manager(test_class, phone, name, role="ic", facility_code="2616"):
    a = """
           %(phone)s > manage %(name)s %(role)s %(code)s
           %(phone)s < %(confirm)s
        """ % {"phone": phone, "name": name, "role": role, "code": facility_code,
               "confirm": Messages.REGISTRATION_CONFIRM % \
                    {"sp_name": SupplyPoint.objects.get(code=facility_code).name,
                     "role": ContactRole.objects.get(code=role).name,
                     "contact_name": name}}
    test_class.runScript(a)
    return Contact.objects.get(name=name)

def _get_resupply_amounts(hsa):
    return [req.sms_format() for req in StockRequest.pending_requests().filter(supply_point=hsa.supply_point)]
    
    
def report_stock(test_class, hsa, product_string, manager=None, products_back=""):
    """
    Reports stock. 
    """
    
    if manager:
        "%(hsa)s needs the following products: %(products)s. Respond 'ready %(hsa_id)s' when products are ready for pick up."
        manager_msg = """
            %(phone)s < %(confirm)s
        """ % {"phone": manager.default_connection.identity,
               "confirm": Messages.SUPERVISOR_SOH_NOTIFICATION % \
                {"hsa": hsa.name,
                 "products": products_back,
                 "hsa_id": hsa.supply_point.code}}
    else: 
        manager_msg = ""
    a = """
           %(phone)s > soh %(products)s
           %(phone)s < %(confirm)s
           %(manager_msg)s
        """ % {"phone": hsa.default_connection.identity, 
               "products": product_string, 
               "confirm": Messages.SOH_ORDER_CONFIRM % {"contact": hsa.name},
               "manager_msg": manager_msg}
    test_class.runScript(a)
    