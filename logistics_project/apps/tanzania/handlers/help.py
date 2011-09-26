from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from django.utils.translation import ugettext as _
from logistics.util import config

class Help(KeywordHandler):
    """
    Default help response.
    """

    keyword = "help|msaada"

    def help(self):
        if hasattr(self.msg, "logistics_contact"):
            self.respond(_(config.Messages.HELP_REGISTERED))
        else:
            self.respond(_(config.Messages.HELP_UNREGISTERED))
