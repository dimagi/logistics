from logistics.app import App as LogisticsApp

class App(LogisticsApp):
    """
    Once upon a time this app overrode some stuff.
    All logic has since been moved into handlers, 
    and this actually does nothing.
    """
    
    def start (self):
        # don't do all the scheduling stuff
        pass
    
    def handle (self, message):
        pass
        
    def default(self, message):
        # the base class overrides all possible responses. 
        # this avoids that problem.
        pass
    
    