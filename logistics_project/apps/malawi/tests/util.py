from logistics.util import config
from logistics.models import SupplyPoint, ContactRole,\
    StockRequest, ProductReportsHelper
from rapidsms.models import Contact
from logistics.const import Reports


def create_hsa(test_class, phone, name, id="1", facility_code="2616", products=None):
    a = """
           %(phone)s > register %(name)s %(id)s %(code)s
           %(phone)s < %(confirm)s
        """ % {"phone": phone, "name": name, "id": id, "code": facility_code,
               "confirm": config.Messages.REGISTRATION_CONFIRM % \
                    {"sp_name": SupplyPoint.objects.get(code=facility_code).name,
                     "role": "hsa",
                     "contact_name": name}}
    test_class.runScript(a)
    if products:
        b = """
               %(phone)s > add %(products)s
               %(phone)s < %(confirm)s
            """ % {"phone": phone,
                   "confirm": config.Messages.ADD_SUCCESS_MESSAGE % {"products": products},
                   "products": products}
        test_class.runScript(b)
    return Contact.objects.get(name=name)

def create_manager(test_class, phone, name, role="ic", facility_code="2616"):

    if role not in config.Roles.DISTRICT_ONLY:
        a = """
               %(phone)s > manage %(name)s %(role)s %(code)s
               %(phone)s < %(confirm)s
            """ % {"phone": phone, "name": name, "role": role, "code": facility_code,
                   "confirm": config.Messages.REGISTRATION_CONFIRM % \
                        {"sp_name": SupplyPoint.objects.get(code=facility_code).name,
                         "role": ContactRole.objects.get(code=role).name,
                         "contact_name": name}}
    else:
        a = """
               %(phone)s > manage %(name)s %(role)s %(code)s
               %(phone)s < %(confirm)s
            """ % {"phone": phone, "name": name, "role": role, "code": facility_code,
                   "confirm": config.Messages.REGISTRATION_DISTRICT_CONFIRM % \
                        {"sp_name": SupplyPoint.objects.get(code=facility_code).name,
                         "role": ContactRole.objects.get(code=role).name,
                         "contact_name": name}}

    test_class.runScript(a)
    return Contact.objects.get(name=name)

def _get_resupply_amounts(hsa):
    return [req.sms_format() for req in StockRequest.pending_requests().filter(supply_point=hsa.supply_point)]
    
    
def report_stock(test_class, hsa, product_string, managers=None, products_back=""):
    """
    Reports stock. 
    """
    stock_report = ProductReportsHelper(SupplyPoint(), Reports.SOH)
    stock_report.parse(product_string)
    product_list = " ".join(stock_report.reported_products()).strip()
    manager_msgs = []
    if managers:
        
        for manager in managers:
            "%(hsa)s needs the following products: %(products)s. Respond 'ready %(hsa_id)s' when products are ready for pick up."
            manager_msgs.append("""
                %(phone)s < %(confirm)s
            """ % {"phone": manager.default_connection.identity,
                   "confirm": config.Messages.SUPERVISOR_SOH_NOTIFICATION % \
                    {"hsa": hsa.name,
                     "products": products_back,
                     "hsa_id": hsa.supply_point.code}})
    a = """
           %(phone)s > soh %(products)s
           %(phone)s < %(confirm)s
           %(manager_msgs)s
        """ % {"phone": hsa.default_connection.identity, 
               "products": product_string, 
               "confirm": config.Messages.SOH_ORDER_CONFIRM % {"products": product_list},
               "manager_msgs": "".join(manager_msgs)}
    test_class.runScript(a)
