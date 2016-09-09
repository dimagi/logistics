from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from logistics.util import config


class RecordResponseHandler(KeywordHandler):
    """
    Record when you make a response
    """
    _responded = False
    
    def respond(self, template, **kwargs):
        super(RecordResponseHandler, self).respond(template, **kwargs)
        self._responded = True
    
    
    @property
    def responded(self):
        return self._responded
