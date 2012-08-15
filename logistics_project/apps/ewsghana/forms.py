""" 
import RegistrationForm from the django_registraton 3rd party app 

This is a little non-DRY with respect to ModelForm functionality
since the 3rd party register app didn't use ModelForm properly
"""
from datetime import datetime
from django import forms
from django.contrib.auth.models import Group
from rapidsms.contrib.locations.models import Location, Point
from logistics.models import Product, SupplyPoint, ProductStock
from logistics_project.apps.web_registration.forms import AdminRegistersUserForm

PROGRAM_ADMIN_GROUP_NAME = 'program_admin'
def _get_program_admin_group():
    return Group.objects.get(name=PROGRAM_ADMIN_GROUP_NAME)

class EWSGhanaWebRegistrationForm(AdminRegistersUserForm): 
    designation = forms.CharField(required=False)
    is_program_admin = forms.BooleanField(label='User is a DHIO', initial=False, required=False)
    is_IT_admin = forms.BooleanField(label='User is an IT administrator (e.g. programmer)', initial=False, required=False)
    
    def __init__(self, *args, **kwargs):
        self.edit_user = None
        if 'user' in kwargs and kwargs['user'] is not None:
            self.edit_user = kwargs['user']
            initial = {}
            if 'initial' in kwargs:
                initial = kwargs['initial']
            if self.edit_user.groups.filter(name=PROGRAM_ADMIN_GROUP_NAME):
                initial['is_program_admin'] = True 
            initial['is_IT_admin'] = self.edit_user.is_superuser
            kwargs['initial'] = initial
            profile = self.edit_user.get_profile()
            if profile.designation is not None:
                initial['designation'] = profile.designation
        return super(EWSGhanaWebRegistrationForm, self).__init__(*args, **kwargs)

    def save(self, profile_callback=None):
        user = super(EWSGhanaWebRegistrationForm, self).save(profile_callback)
        user.is_staff = False # Can never log into admin site
        pag = _get_program_admin_group()
        if self.cleaned_data['is_program_admin']:
            user.groups.add(pag)
        elif pag in user.groups.all():
            user.groups.remove(pag)
        if self.cleaned_data['is_IT_admin']:
            user.is_superuser = True
        else:
            user.is_superuser = False
        user.save()
        if 'designation' in self.cleaned_data:
            profile = user.get_profile()
            profile.designation = self.cleaned_data['designation']
            profile.save()
        return user

class FacilityForm(forms.ModelForm):
    latitude = forms.DecimalField(required=False)
    longitude = forms.DecimalField(required=False)
    
    class Meta:
        model = SupplyPoint
        exclude = ("last_reported", "groups", "supervised_by")
    
    def __init__(self, *args, **kwargs):
        kwargs['initial'] = {}
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
        commodities = Product.objects.filter(is_active=True).order_by('name')
        for commodity in commodities:
            if commodity.sms_code in self.data:
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
    