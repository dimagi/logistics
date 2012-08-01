from logistics.reports import ProductAvailabilitySummary
from logistics.models import Product
from logistics_project.apps.malawi.warehouse.models import ProductAvailabilityData
from datetime import datetime


class WarehouseProductAvailabilitySummary(ProductAvailabilitySummary):
    """
    Product availability summary, coming from the Malawi data warehouse models.
    """
    def __init__(self, supply_point, width=900, height=300):
        """
        Override the ProductAvailabilitySummary object to work off 
        the warehouse tables.
        """
        self._width = width
        self._height = height
        self._supply_point = supply_point
        
        products = Product.objects.all().order_by('sms_code')
        data = []
        now = datetime.utcnow()
        # TODO: this could now be historical if we wanted
        # TODO: make this use the real date, not the dummy date
        # date = datetime(now.year, now.month, 1)
        from logistics_project.apps.malawi.warehouse.views import _get_window_date
        date = _get_window_date()
        for p in products:
            availability_data = ProductAvailabilityData.objects.get\
                (supply_point=supply_point, date=date, product=p)
            
            data.append({"product": p,
                         "total": availability_data.managed,
                         "with_stock": availability_data.managed_and_with_stock,
                         "without_stock": availability_data.managed_and_without_stock,
                         "without_data": availability_data.managed_and_without_data})
        self.data = data
        