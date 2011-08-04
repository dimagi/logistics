#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from django.utils.translation import ugettext_noop as _
from logistics.apps.logistics.util import config
        
class YesHelpHandler(KeywordHandler):
    """
    Just a little helper to refer people to the other keywords in case they get lost
    """

    keyword = "yes|ndio|ndyo"    

    def help(self):
        self.handle("")

    def handle(self, text):
        self.respond(_(config.Messages.YES_HELP))