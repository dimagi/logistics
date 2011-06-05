#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django import forms
from django.conf import settings
from django.utils.translation import ugettext as _
from rapidsms.contrib.locations.models import Point
from .models import SupplyPoint, Product, ProductStock

class FacilityForm(forms.ModelForm):
    commodities = forms.ModelMultipleChoiceField(Product.objects.all().order_by('name'), 
                                                 help_text='Select only commodities actively stocked by this facility', 
                                                 required=False)
    latitude = forms.DecimalField(required=False)
    longitude = forms.DecimalField(required=False)
    
    class Meta:
        model = SupplyPoint
        exclude = ("last_reported", )
    
    def __init__(self, *args, **kwargs):
        kwargs['initial'] = {'commodities': [0,1,2,3]}
        if 'instance' in kwargs and kwargs['instance']:
            initial_sp = kwargs['instance']
            if 'initial' not in kwargs:
                kwargs['initial'] = {}
            pss = ProductStock.objects.filter(supply_point=initial_sp, 
                                              is_active=True)
            kwargs['initial']['commodities'] = [p.product.pk for p in pss]
            if initial_sp.location and initial_sp.location.point:
                kwargs['initial']['latitude'] = initial_sp.location.point.latitude
                kwargs['initial']['longitude'] = initial_sp.location.point.longitude
        super(FacilityForm, self).__init__(*args, **kwargs)
                
    def save(self, *args, **kwargs):
        facility = super(FacilityForm, self).save(*args, **kwargs)
        if self.cleaned_data['commodities']:
            for commodity in Product.objects.all():
                if commodity in self.cleaned_data['commodities']:
                    ps, created = ProductStock.objects.get_or_create(supply_point=facility, 
                                                                     product=commodity)
                    ps.is_active = True
                    ps.save()
                else:
                    try:
                        ps = ProductStock.objects.get(supply_point=facility, 
                                                      product=commodity)
                    except ProductStock.DoesNotExist:
                        # great
                        pass
                    else:
                        # if we have stock info, we keep it around just in case
                        # but we mark it as inactive
                        ps.is_active = False
                        ps.save()
        if self.cleaned_data['latitude'] and self.cleaned_data['longitude']:
            lat = self.cleaned_data['latitude']
            lon = self.cleaned_data['longitude']
            point, created = Point.objects.get_or_create(latitude=lat, longitude=lon)
            if facility.location is None:
                facility.location = Location.objects.create(name=facility.name, 
                                                            code=facility.code)
            facility.location.point = point
            facility.location.save()
        elif not self.cleaned_data['latitude'] and not self.cleaned_data['longitude']:
            if facility.location.point is not None:
                facility.location.point = None
                facility.location.save()
        return facility
    
class CommodityForm(forms.ModelForm):
    class Meta:
        model = Product

