from logistics.util import config
from logistics.models import ProductReportType, ContactRole
from logistics.const import Reports
    
def load_report_types():
    """
    Loads report types from config
    """
    for code, name in list(Reports.ALL_REPORTS.items()):
        prod = ProductReportType.objects.get_or_create(code=code)[0]
        if prod.name != name:
            prod.name = name
            prod.save()
    
def load_roles():
    """
    Loads roles from config
    """
    for code, name in list(config.Roles.ALL_ROLES.items()):
        role = ContactRole.objects.get_or_create(code=code)[0]
        if role.name != name:
            role.name = name
            role.save()
    
    