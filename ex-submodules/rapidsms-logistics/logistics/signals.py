from datetime import datetime

def post_save_product_report(sender, instance, created, **kwargs):
    """
    Every time a product report is created,
    1. Update the facility information
    2. Update the facility stock information
    """
    if not created:             return
    from logistics.apps.logistics.models import ProductStock, Facility, \
        STOCK_ON_HAND_REPORT_TYPE
    if instance.report_type.code == STOCK_ON_HAND_REPORT_TYPE:
        try:
            productstock = ProductStock.objects.get(supply_point=instance.supply_point,
                                                    product=instance.product)
        except ProductStock.DoesNotExist:
            productstock = ProductStock(is_active=False, supply_point=instance.supply_point,
                                        product=instance.product)
        productstock.quantity = instance.quantity
        productstock.save()
    instance.supply_point.last_reported = datetime.now()
    instance.supply_point.save()

