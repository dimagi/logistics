from django.db import transaction
from django.dispatch import Signal

stockout_reported = Signal(providing_args=["supply_point", "products", "reported_by"])
stockout_resolved = Signal(providing_args=["supply_point", "products", "resolved_by"])

def notify_suppliees_of_stockouts_resolved(sender, supply_point, products, resolved_by, **kwargs):
    supply_point.notify_suppliees_of_stockouts_resolved([p.code for p in products], 
                                                        exclude=None if resolved_by is None else [resolved_by])
    
def notify_suppliees_of_stockouts_reported(sender, supply_point, products, reported_by, **kwargs):
    supply_point.notify_suppliees_of_stockouts_reported([p.code for p in products], 
                                                        exclude=None if reported_by is None else [reported_by])

@transaction.commit_on_success
def post_save_stock_transaction(sender, instance, created, **kwargs):
    from logistics.models import ProductStock
    ps = ProductStock.objects.get(supply_point=instance.supply_point, 
                                  product=instance.product)
    ps.update_auto_consumption()

@transaction.commit_on_success
def post_save_product_report(sender, instance, created, **kwargs):
    """
    Every time a product report is created,
    1. Update the facility report date information
    2. update the stock information at the given facility
    3. Generate a stock transaction
    
    I guess 1+3 could go on a stocktransaction signal. 
    Something to consider if we start saving stocktransactions anywhere else.
    """
    instance.post_save(created)

def create_user_profile(sender, instance, created, **kwargs):
    """Create a matching profile whenever a User is created."""
    if created:
        from logistics.models import LogisticsProfile
        profile, new = LogisticsProfile.objects.get_or_create(user=instance)
