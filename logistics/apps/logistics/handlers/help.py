from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from django.utils.translation import ugettext as _

class Help(KeywordHandler):
    keyword = "help"

    def help(self):
        self.respond(_('Welcome to EWS. Available commands are help, stop, soh, rec'))
