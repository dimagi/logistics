from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.contrib.handlers.handlers.tagging import TaggingHandler
from logistics.decorators import logistics_contact_required
from logistics.util import config
from django.utils.translation import ugettext_noop as _


class Trans(KeywordHandler, TaggingHandler):
    keyword = "trans"

    def help(self):
        self.respond(_(config.Messages.TRANS_HANDLER_HELP))

    @logistics_contact_required()
    def handle(self):
        #TODO
        pass