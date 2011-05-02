from logistics.apps.malawi.const import Operations
from logistics.apps.logistics.models import ContactRole
from logistics.apps.malawi import const


def user_can_do(contact, operation):
    # one might want to use the responsibilities framework to manage
    # this but currently it seems strange that we'd have such tight
    # coupling between app logic and database logic, so it's here
    if not contact.is_active:
        return False
    if operation == Operations.REPORT_STOCK:
        return contact.role == ContactRole.objects.get(code=const.Roles.HSA)
    if operation == Operations.FILL_ORDER:
        return contact.role == ContactRole.objects.get(code=const.Roles.IN_CHARGE)
    if operation == Operations.MAKE_TRANSFER:
        return contact.role == ContactRole.objects.get(code=const.Roles.HSA)
    if operation == Operations.CONFIRM_TRANSFER:
        return contact.role == ContactRole.objects.get(code=const.Roles.HSA)
    if operation == Operations.REPORT_FOR_OTHERS:
        return contact.role == ContactRole.objects.get(code=const.Roles.IN_CHARGE)
    # TODO, fill this in more
    return True