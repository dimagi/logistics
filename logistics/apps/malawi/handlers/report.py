from logistics.apps.logistics.models import ProductReportsHelper, StockRequest
from django.utils.translation import ugettext as _
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from logistics.apps.malawi.const import Messages, Operations
from logistics.apps.malawi import util
from logistics.apps.logistics.const import Reports
from logistics.apps.logistics.decorators import logistics_contact_and_permission_required

class ReportRegistrationHandler(KeywordHandler):
    """
    Report stock on hand or a receipt for someone else
    """
    
    keyword = "report"
    
    def help(self):
        self.respond(_(Messages.REPORT_HELP))
        
    
    @logistics_contact_and_permission_required(Operations.REPORT_FOR_OTHERS)
    def handle(self, text):
    
        words = text.split(" ")
        if len(words) < 2:
            return self.help()
        
        hsa_id = words[0]
        keyword = words[1].lower()
        report_data = " ".join(words[2:])
        hsa = util.get_hsa(hsa_id)
        if hsa is None:
            self.respond(Messages.UNKNOWN_HSA, hsa_id=hsa_id)
        elif keyword not in [Reports.SOH, Reports.REC]:
            self.respond(Messages.BAD_REPORT_KEYWORD, keyword=hsa_id)
        else:
            # we've got an hsa, we've got a keyword, let's rock 
            # NOTE: a lot of this logic is copy-pasted from the soh
            # and rec workflows. It would be good if this were 
            # abstracted better.
            stock_report = ProductReportsHelper(hsa.supply_point, 
                                                keyword, self.msg.logger_msg)
            stock_report.parse(report_data)
            stock_report.save()
            if keyword == Reports.SOH:
                # create pending requests
                requests = StockRequest.create_from_report(stock_report, hsa)
            else:
                assert(keyword == Reports.REC)
                # or close pending requests
                requests = StockRequest.close_pending_from_receipt_report(stock_report, self.msg.logistics_contact)
            
            if stock_report.errors:
                # TODO: respond better.
                self.respond(Messages.GENERIC_ERROR)
            else:
                
                if keyword == Reports.SOH:
                    self.respond(Messages.REPORT_SOH_RESPONSE, 
                                 hsa=hsa.name,
                                 products=", ".join(req.sms_format() for req in requests),
                                 hsa_id=hsa.supply_point.code)
                
                else:
                    assert(keyword == Reports.REC)
                    self.respond(Messages.REPORT_RECEIPT_RESPONSE, 
                                 reporter=self.msg.logistics_contact.name,
                                 hsa=hsa.name,
                                 products=" ".join(stock_report.reported_products()).strip())
                
                