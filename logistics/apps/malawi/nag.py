from datetime import datetime
from logistics.apps.logistics.models import ProductReport, ProductReportType, SupplyPoint

def get_non_reporting_hsas():
    hsas = set(SupplyPoint.objects.filter(type=SupplyPointType.objects.get(code='hsa')))
    reporters = set(lambda x: x.supply_point,
                    ProductReport.objects.filter(type=ProductReportType.objects.get(code='soh'),
                                                report_date__range = [datetime.now().replace(month=datetime.today().month - 1),
                                                                      datetime.now()]))
    return hsas.difference(reporters)