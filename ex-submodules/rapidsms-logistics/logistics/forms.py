#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django import forms
from django.conf import settings
from django.utils.translation import ugettext as _
from .models import Facility, Product

class FacilityForm(forms.ModelForm):
    class Meta:
        model = Facility

class CommodityForm(forms.ModelForm):
    class Meta:
        model = Product

