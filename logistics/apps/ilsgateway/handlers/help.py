from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from django.utils.translation import ugettext as _

class Help(KeywordHandler):
    """
    """

    keyword = "help|msaada"

    def help(self):
        try:
            self.msg.contact.contactdetail
            self.respond(_('Welcome to ILSGateway. Available commands are soh, delivered, not delivered, submitted, not submitted, language, sw, en, stop, supervision, la'))
        except:             
            self.respond(_("To register, send register <name> <msd code>. Example: register 'john patel d34002'"))
