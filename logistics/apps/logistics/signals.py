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
            productstock = ProductStock.objects.get(facility=instance.facility,
                                                    product=instance.product)
        except ProductStock.DoesNotExist:
            productstock = ProductStock(is_active=False, facility=instance.facility,
                                        product=instance.product)
        productstock.quantity = instance.quantity
        productstock.save()
    instance.facility.last_reported = datetime.now()
    instance.facility.save()

def create_user_profile(sender, instance, created, **kwargs):
    """Create a matching profile whenever a User is created."""
    if created:
        from logistics.apps.logistics.models import LogisticsProfile
        profile, new = LogisticsProfile.objects.get_or_create(user=instance)
