from logistics.apps.logistics.app import App as LogisticsApp, SOH_KEYWORD

class App(LogisticsApp):
    """
    This app overrides the base functionality of the logistics app, allowing 
    us to do custom logic for Malawi
    """
    
    
    def start (self):
        # don't do all the scheduling stuff
        pass
    
    def handle (self, message):
        # we override the builtin logic here. ideally this would call the
        # base class first, but there's a lot of cruft in there currently
        should_proceed, return_code = self._check_preconditions(message)
        if not should_proceed:
            return return_code
        # todo: the malawi workflow goes here.
        pass
    
    
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
    