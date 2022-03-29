#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from __future__ import unicode_literals
from builtins import object
from django import forms
from .models import *


class ContactForm(forms.ModelForm):
    class Meta(object):
        model = Contact
#        exclude = ("connections",)
class ConnectionForm(forms.ModelForm):
    class Meta(object):
        model = Connection
        exclude = ("contact",)