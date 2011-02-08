from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from django.utils.translation import ugettext as _

class Help(KeywordHandler):
    keyword = "help"

    def help(self):
        self.respond(_('Welcome to ILSGateway. Available commands are soh, delivered, not delivered, submitted, not submitted, language, sw, en, stop, supervision, la'))
