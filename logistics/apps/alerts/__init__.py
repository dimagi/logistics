
class Alert(object):
    """
    An alert, for display on the dashboard.
    """
    
    def __init__(self, text, url=None):
        self._text = text
        self._url = url
        
        
    @property
    def url(self):
        return self._url
    
    @property
    def text(self):
        return self._text