from django.conf import settings
from django.utils.importlib import import_module
const = import_module(settings.CONST)
from logistics.apps.logistics.models import ContactRole


def has_permissions_to(contact, operation):
    # one might want to use the responsibilities framework to manage
    # this but currently it seems strange that we'd have such tight
    # coupling between app logic and database logic, so it's here
    if not contact.is_active:
        return False
    if operation == const.Operations.REPORT_STOCK:
        return contact.role == ContactRole.objects.get(code=const.Roles.HSA)
    if operation == const.Operations.FILL_ORDER:
        return contact.role == ContactRole.objects.get(code=const.Roles.IN_CHARGE)
    if operation == const.Operations.MAKE_TRANSFER:
        return contact.role == ContactRole.objects.get(code=const.Roles.HSA)
    if operation == const.Operations.CONFIRM_TRANSFER:
        return contact.role == ContactRole.objects.get(code=const.Roles.HSA)
    if operation == const.Operations.REPORT_FOR_OTHERS:
        return contact.role == ContactRole.objects.get(code=const.Roles.IN_CHARGE)
    # TODO, fill this in more
    return True