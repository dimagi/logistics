from logistics.models import SupplyPoint
from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from rapidsms.contrib.handlers.handlers.tagging import TaggingHandler
from django.utils.translation import ugettext_noop as _
from logistics.util import config

class Arrived(KeywordHandler, TaggingHandler):
    keyword = "arrived|aliwasili"

    def help(self):
        self.handle(text="")

    def handle(self, text):
        words = text.split()
        if len(words) != 1:
            self.respond_error(_(config.Messages.ARRIVED_HELP))
            return True

        msdcode = words[0]
        try:
            sp = SupplyPoint.objects.get(code__iexact=msdcode)
            # we still use respond error because we want it to show up in the unrecognized message log
            self.respond(_(config.Messages.ARRIVED_KNOWN), facility=sp.name)
        except SupplyPoint.DoesNotExist:
            self.respond(_(config.Messages.ARRIVED_DEFAULT))
        return True
