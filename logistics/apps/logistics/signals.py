import logging
from datetime import datetime
from django.db import transaction

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
    """ 1. Update the facility report date information """
    instance.facility.last_reported = datetime.now()
    instance.facility.save()
    """ 2. update the stock information at the given facility """
    beginning_balance = instance.facility.stock(instance.product)
    if instance.report_type.code == STOCK_ON_HAND_REPORT_TYPE:
        instance.facility.update_stock(instance.product, instance.quantity)
    """ 3. Generate a stock transaction """
    st = StockTransaction.from_product_report(instance, beginning_balance)
    if st is not None:
        st.save()

def create_user_profile(sender, instance, created, **kwargs):
    """Create a matching profile whenever a User is created."""
    if created:
        from logistics.apps.logistics.models import LogisticsProfile
        profile, new = LogisticsProfile.objects.get_or_create(user=instance)
