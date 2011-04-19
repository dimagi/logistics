import logging
from datetime import datetime
from django.db import transaction
from django.dispatch import Signal

stockout_resolved = Signal(providing_args=["supply_point", "products", "resolved_by"])

def notify_suppliees_of_stockouts_resolved(sender, supply_point, products, resolved_by):
    exclude_list = [] if resolved_by is None else [resolved_by]
    supply_point.notify_suppliees_of_stockouts_resolved([p.code for p in products], 
                                                        exclude=exclude_list)
    
# why are these here?
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
    if not created:             return
    from logistics.apps.logistics.models import ProductStock, Facility, \
        STOCK_ON_HAND_REPORT_TYPE, RECEIPT_REPORT_TYPE, StockTransaction
    
    # 1. Update the facility report date information 
    instance.supply_point.last_reported = datetime.now()
    instance.supply_point.save()
    # 2. update the stock information at the given facility """
    beginning_balance = instance.supply_point.stock(instance.product)

    if instance.report_type.code == STOCK_ON_HAND_REPORT_TYPE:
        instance.supply_point.update_stock(instance.product, instance.quantity)
    
    st = StockTransaction.from_product_report(instance, beginning_balance)
    if st is not None:
        st.save()

def create_user_profile(sender, instance, created, **kwargs):
    """Create a matching profile whenever a User is created."""
    if created:
        from logistics.apps.logistics.models import LogisticsProfile
        profile, new = LogisticsProfile.objects.get_or_create(user=instance)
