#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django import forms
from django.conf import settings
from django.utils.translation import ugettext as _
from .models import Facility, Product, ProductStock

class FacilityForm(forms.ModelForm):
    commodities = forms.ModelMultipleChoiceField(Product.objects.all().order_by('name'), 
                                                 help_text='Select only commodities actively stocked by this facility', 
                                                 required=False)
    
    class Meta:
        model = Facility
    
    def __init__(self, *args, **kwargs):
        kwargs['initial'] = {'commodities': [0,1,2,3]}
        if 'instance' in kwargs:
            if 'initial' not in kwargs:
                kwargs['initial'] = {}
            pss = ProductStock.objects.filter(supply_point=kwargs['instance'], 
                                              is_active=True)
            kwargs['initial']['commodities'] = [p.product.pk for p in pss]
        super(FacilityForm, self).__init__(*args, **kwargs)
                
    def save(self, *args, **kwargs):
        facility = super(FacilityForm, self).save(*args, **kwargs)
        if self.cleaned_data['commodities']:
            for commodity in Product.objects.all():
                if commodity in self.cleaned_data['commodities']:
                    ps, created = ProductStock.objects.get_or_create(facility=facility, 
                                                                     product=commodity)
                    ps.is_active = True
                    ps.save()
                else:
                    try:
                        ps = ProductStock.objects.get(facility=facility, 
                                                      product=commodity)
                    except ProductStock.DoesNotExist:
                        # great
                        pass
                    else:
                        # if we have stock info, we keep it around just in case
                        # but we mark it as inactive
                        ps.is_active = False
                        ps.save()
        return facility
    
class CommodityForm(forms.ModelForm):
    class Meta:
        model = Product

