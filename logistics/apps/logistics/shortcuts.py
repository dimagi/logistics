from logistics.apps.logistics.models import ProductReportsHelper

def create_stock_report(report_type, supply_point, text, logger_msg=None):
    """
    Gets a stock report helper object parses it, and saves it.
    """
    stock_report = ProductReportsHelper(supply_point, 
                                        report_type,  
                                        logger_msg)
    stock_report.parse(text)
    stock_report.save()
    return stock_report

