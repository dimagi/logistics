#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from django.utils.translation import ugettext as _
from logistics.util import config
from logistics.decorators import logistics_contact_required
from logistics.shortcuts import create_stock_report
from logistics.const import Reports
import logging

class LostAdjusted(KeywordHandler):
    """
    Losses and adjustments
    """
    
    keyword = "la|um"
    
    def help(self):
        self.respond(_(config.Messages.LOSS_ADJUST_HELP))

    @logistics_contact_required()
    def handle(self, text):
        contact = self.msg.logistics_contact
        sp = self.msg.logistics_contact.supply_point
        stock_report = create_stock_report(Reports.LOSS_ADJUST,  
                                           sp,
                                           text, 
                                           self.msg.logger_msg,
                                           timestamp=self.msg.timestamp)
        
        if stock_report.errors:
            self.respond(_(config.Messages.LOSS_ADJUST_BAD_FORMAT))
            return
    
        else:    
            self.respond(_(config.Messages.LOSS_ADJUST_CONFIRM))