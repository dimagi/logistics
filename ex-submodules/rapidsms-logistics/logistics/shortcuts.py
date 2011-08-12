from logistics.models import ProductReportsHelper, SupplyPoint

def create_stock_report(report_type, supply_point, text, logger_msg=None, 
                        timestamp=None):
    """
    Gets a stock report helper object parses it, and saves it.
    """
    stock_report = ProductReportsHelper(supply_point, 
                                        report_type,  
                                        logger_msg, 
                                        timestamp)
    stock_report.newparse(text)
    stock_report.save()
    return stock_report

def supply_point_from_location(loc, type, parent=None):
    """
    This utility is used by the loaders to create supply points from locations
    """
    try:
        sp = SupplyPoint.objects.get(location=loc, type=type)
    except SupplyPoint.DoesNotExist:
        sp = SupplyPoint(location=loc)
    sp.name = loc.name
    sp.active = True
    sp.type = type
    sp.code = loc.code
    sp.supplied_by = parent
    try:
        sp.save()
    except:
        print sp
        raise
    
    return sp

