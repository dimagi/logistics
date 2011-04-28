from logistics.apps.malawi.const import Messages
from logistics.apps.logistics.models import SupplyPoint, ContactRole
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