from warehouse.runner import WarehouseRunner
from logistics_project.apps.tanzania.reporting.run_reports import populate_report_data,\
    clear_out_reports


class TanzaniaWarehouseRunner(WarehouseRunner):
    """
    Tanzania's implementation of the warehouse runner. 
    """
    
    def cleanup(self, start, end):
        """
        Cleanup all warehouse data between start and end.
        """
        clear_out_reports(start, end)
    
    def generate(self, run_record):
        """
        Generate all warehouse data between start and end.
        """
        populate_report_data(run_record.start, run_record.end)
    