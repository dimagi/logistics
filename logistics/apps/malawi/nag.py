from datetime import datetime
from logistics.apps.logistics.models import ProductReport, ProductReportType, SupplyPoint,\
    SupplyPointType
from logistics.apps.logistics.const import Reports

def get_non_reporting_hsas(since):
    """
    Get all HSAs who haven't reported since a passed in date
    """
    hsas = set(SupplyPoint.objects.filter(type=SupplyPointType.objects.get(code='hsa')))
    reporters = set(x.supply_point for x in \
                    ProductReport.objects.filter(report_type=ProductReportType.objects.get(code=Reports.SOH),
                                                 report_date__range = [since,
                                                                       datetime.utcnow()]))
    return hsas - reporters