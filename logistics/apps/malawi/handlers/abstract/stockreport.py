from logistics.apps.malawi.const import Messages, Operations
from logistics.apps.malawi.handlers.abstract.base import RecordResponseHandler
from logistics.apps.logistics.models import ProductReportsHelper, StockRequest
from django.db import transaction
from logistics.apps.logistics.decorators import logistics_contact_and_permission_required


class StockReportBaseHandler(RecordResponseHandler):
    hsa = None
    requests = []
    
    
    def get_report_type(self):
        raise NotImplemented("This method must be overridden")
    
    def send_responses(self):
        raise NotImplemented("This method must be overridden")
    
    @transaction.commit_on_success
    @logistics_contact_and_permission_required(Operations.REPORT_STOCK)
    def handle(self, text):
        """
        Check some precondidtions, based on shared assumptions of these handlers.
        Return true if there is a precondition that wasn't met. If all preconditions
        are met, the variables for facility and name will be set.
        
        This method will manage some replies as well.
        """
        # at some point we may want more granular permissions for these
        # operations, but for now we just share the one

        self.hsa = self.msg.logistics_contact
        
        stock_report = ProductReportsHelper(self.hsa.supply_point, 
                                            self.get_report_type(),  
                                            self.msg.logger_msg)
        stock_report.parse(text)
        stock_report.save()
        self.requests = StockRequest.create_from_report(stock_report, self.hsa)
        self.send_responses(stock_report)        