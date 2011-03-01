from datetime import datetime

def post_save_product_report(sender, instance, created, **kwargs):
    """
    Every time a product report is created,
    1. Update the facility information
    2. Update the facility stock information
    """
    if not created:             return
    from logistics.apps.logistics.models import ProductStock, Facility
    try:
        productstock = ProductStock.objects.get(facility=instance.facility,
                                                product=instance.product)
    except ProductStock.DoesNotExist:
        productstock = ProductStock(is_active=False, facility=instance.facility,
                                    product=instance.product)
    if productstock.quantity == 0 and instance.quantity > 0:
        # a stockout has been resolved!
        # notify all facilities supplied by this one
        to_notify = Facility.objects.filter(supplied_by=instance.facility).distinct()
        for fac in to_notify:
            reporters = fac.reporters()
            for reporter in reporters:
                send_message(reporter.default_connection,
                            "Dear %(name)s, the stockout of %(product)s at %(facility)s has been resolved." %
                             {'name':reporter.name,
                             'product':instance.product.name,
                             'facility':instance.facility.name})
    productstock.quantity = instance.quantity
    productstock.save()
    instance.facility.last_reported = datetime.now()
    instance.facility.save()

