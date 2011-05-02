from logistics.apps.logistics.signals import stockout_resolved

def notify_suppliees_of_stockouts_resolved(sender, supply_point, products, 
                                           resolved_by, **kwargs):
    """
    Notifies suppliees of stockouts being resolved.
    """
    exclude_list = [] if resolved_by is None else [resolved_by]
    supply_point.notify_suppliees_of_stockouts_resolved([p.code for p in products], 
                                                        exclude=exclude_list)
    
stockout_resolved.connect(notify_suppliees_of_stockouts_resolved)