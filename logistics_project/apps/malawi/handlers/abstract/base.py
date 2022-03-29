from __future__ import unicode_literals
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler


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
