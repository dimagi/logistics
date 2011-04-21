from logistics.apps.logistics.app import App as LogisticsApp, SOH_KEYWORD
from logistics.apps.logistics.models import ProductReportsHelper,\
    STOCK_ON_HAND_REPORT_TYPE, GET_HELP_MESSAGE, StockRequest,\
    StockRequestStatus, ContactRole
from logistics.apps.logistics.errors import UnknownCommodityCodeError
from django.conf import settings
from django.db import transaction
from logistics.apps.malawi import const
from rapidsms.models import Contact

ORDER_CONFIRM = "Thank you %(contact)s. The health center in charge has been notified and you will receive an alert when supplies are ready." 
NO_IN_CHARGE = "There is no in-charge registered for %(supply_point)s. Please contact your supervisor to resolve this."
SUPERVISOR_NOTIFICATION = "%(hsa)s needs the following supplies: %(supplies)s. Respond 'ready %(hsa_id)s' when supplies are ready"
                                
class App(LogisticsApp):
    """
    This app overrides the base functionality of the logistics app, allowing 
    us to do custom logic for Malawi
    """
    
    
    def start (self):
        # don't do all the scheduling stuff
        pass
    
    @transaction.commit_on_success()
    def handle (self, message):
        # we override the builtin logic here. ideally this would call the
        # base class first, but there's a lot of cruft in there currently
        should_proceed, return_code = self._check_preconditions(message)
        if not should_proceed:
            return return_code
        try:
            sp = message.logistics_contact.supply_point
            stock_report = ProductReportsHelper(sp, STOCK_ON_HAND_REPORT_TYPE,  
                                                message.logger_msg)
            stock_report.parse(self._clean_message(message.text))
            stock_report.save()
            requests = StockRequest.create_from_report(stock_report, message.logistics_contact)
            if stock_report.errors:
                self._send_error_response(message, stock_report)
            else:
                # normal malawi logic goes here
                try:
                    supervisor = Contact.objects.get(role=ContactRole.objects.get(code=const.ROLE_IN_CHARGE), 
                                                     supply_point=sp.supplied_by)
                    supervisor.message(SUPERVISOR_NOTIFICATION, 
                                       hsa=message.logistics_contact.name,
                                       supplies=", ".join(req.sms_format() for req in requests),
                                       hsa_id=message.logistics_contact.supply_point.code)
                    message.respond(ORDER_CONFIRM,
                                    contact=message.logistics_contact.name)
                
                except Contact.DoesNotExist:
                    message.respond(NO_IN_CHARGE,
                                    supply_point=message.logistics_contact.supply_point.supplied_by.name)
                
                    
                #self._send_responses(message, stock_report)
            return True
        except Exception, e:
            if settings.DEBUG:
                # this error actually gets logged deep within rapidSMS
                message.respond(unicode(e))
            raise
    
    def default(self, message):
        # the base class overrides all possible responses. 
        # this avoids that problem.
        pass
    
    def _should_handle(self, message):
        """ 
        Tests whether this message is one which should go through the handle phase.
        Currently only SOH keyword is supported.
        """
        return message.text.lower().split(" ") and message.text.lower().split(" ")[0] == SOH_KEYWORD
    