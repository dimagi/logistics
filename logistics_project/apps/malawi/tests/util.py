from logistics.util import config
from logistics.models import SupplyPoint, ContactRole, \
    StockRequest, ProductReportsHelper, format_product_string
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

def create_manager(test_class, phone, name, role="ic", supply_point_code="2616"):

    if role in config.Roles.FACILITY_ONLY:
        a = """
               %(phone)s > manage %(name)s %(role)s %(code)s
               %(phone)s < %(confirm)s
            """ % {"phone": phone, "name": name, "role": role, "code": supply_point_code,
                   "confirm": config.Messages.REGISTRATION_CONFIRM % \
                        {"sp_name": SupplyPoint.objects.get(code=supply_point_code).name,
                         "role": ContactRole.objects.get(code=role).name,
                         "contact_name": name}}
    elif role in config.Roles.DISTRICT_ONLY:
        a = """
               %(phone)s > manage %(name)s %(role)s %(code)s
               %(phone)s < %(confirm)s
            """ % {"phone": phone, "name": name, "role": role, "code": supply_point_code,
                   "confirm": config.Messages.REGISTRATION_DISTRICT_CONFIRM % \
                        {"sp_name": SupplyPoint.objects.get(code=supply_point_code).name,
                         "role": ContactRole.objects.get(code=role).name,
                         "contact_name": name}}
    elif role in config.Roles.ZONE_ONLY:
        a = """
               %(phone)s > manage %(name)s %(role)s %(code)s
               %(phone)s < %(confirm)s
            """ % {
                "phone": phone,
                "name": name,
                "role": role,
                "code": supply_point_code,
                "confirm": config.Messages.REGISTRATION_ZONE_CONFIRM % {
                    "contact_name": name,
                    "role": ContactRole.objects.get(code=role).name,
                    "sp_name": SupplyPoint.objects.get(code=supply_point_code).name,
                }
            }
    else:
        raise config.Roles.InvalidRoleException(role)

    test_class.runScript(a)
    return Contact.objects.get(name=name)

def _get_resupply_amounts(hsa):
    return [req.sms_format() for req in StockRequest.pending_requests().filter(supply_point=hsa.supply_point)]
    
    
def report_stock(test_class, hsa, product_string, managers=None, products_back=""):
    """
    Reports stock. 
    """
    stock_report = ProductReportsHelper(SupplyPoint(), Reports.SOH)
    stock_report.newparse(product_string)
    product_list = format_product_string(stock_report.reported_products())
    manager_msgs = []
    if managers:
        
        for manager in managers:
            "%(hsa)s needs the following products: %(products)s. Respond 'ready %(hsa_id)s' when products are ready for pick up."
            manager_msgs.append("""
                %(phone)s < %(confirm)s
            """ % {"phone": manager.default_connection.identity,
                   "confirm": config.Messages.SUPERVISOR_HSA_LEVEL_SOH_NOTIFICATION % \
                    {"hsa": hsa.name,
                     "products": products_back,
                     "hsa_id": hsa.supply_point.code}})
    a = """
           %(phone)s > soh %(products)s
           %(phone)s < %(confirm)s
           %(manager_msgs)s
        """ % {"phone": hsa.default_connection.identity, 
               "products": product_string, 
               "confirm": config.Messages.SOH_HSA_LEVEL_ORDER_CONFIRM % {"products": product_list},
               "manager_msgs": "".join(manager_msgs)}
    test_class.runScript(a)


def report_facility_level_stock(test_class, reporter, product_string, managers, resupply_amounts):
    """
    Reports stock in the facility-level workflow.
    """
    stock_report = ProductReportsHelper(reporter.supply_point, Reports.SOH)
    stock_report.newparse(product_string)
    product_list = " ".join(stock_report.reported_products()).strip()

    manager_msgs = []
    if managers:
        resupplies = []
        for product_code in stock_report.product_stock.keys():
            if product_code in resupply_amounts:
                resupplies.append(product_code + " " + str(resupply_amounts[product_code]))
        test_class.assertEqual(len(resupply_amounts), len(resupplies))

        for manager in managers:
            manager_msgs.append("""
                %(phone)s < %(confirm)s
            """ % {"phone": manager.default_connection.identity,
                   "confirm": config.Messages.SUPERVISOR_FACILITY_LEVEL_SOH_NOTIFICATION % \
                    {"supply_point": reporter.supply_point.name,
                     "products": ", ".join(resupplies),
                     "supply_point_code": reporter.supply_point.code}})

    a = """
           %(phone)s > soh %(products)s
           %(phone)s < %(confirm)s
           %(manager_msgs)s
        """ % {"phone": reporter.default_connection.identity,
               "products": product_string,
               "confirm": config.Messages.SOH_FACILITY_LEVEL_ORDER_CONFIRM % {"products": product_list},
               "manager_msgs": "".join(manager_msgs)}
    test_class.runScript(a)
