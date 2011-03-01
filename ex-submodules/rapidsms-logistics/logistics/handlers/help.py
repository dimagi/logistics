#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from rapidsms.contrib.handlers.handlers.keyword import KeywordHandler
from django.utils.translation import ugettext as _

class Help(KeywordHandler):
    keyword = "help"

    def help(self):
        self.respond(_('Welcome to Early Warning System. Available commands are soh, rec, help, stop. You can send "help <command>" to get help on a specific command. Eg. "Help soh'))
