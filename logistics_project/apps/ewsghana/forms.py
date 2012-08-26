""" 
import RegistrationForm from the django_registraton 3rd party app 

This is a little non-DRY with respect to ModelForm functionality
since the 3rd party register app didn't use ModelForm properly

A note on how permissions are set up:
default -> view only
associated with a facility -> can input stock for that facility
member of django group 'facility_managers' -> can add/remove/edit users and facilities
user.is_superuser -> as above, plus can modify commdities globally
"""
from datetime import datetime
from django import forms
from django.contrib.auth.models import Group
from rapidsms.contrib.locations.models import Location, Point
from rapidsms.conf import settings
from rapidsms.models import Contact
from logistics.models import Product, SupplyPoint, ProductStock
from logistics_project.apps.ewsghana.permissions import FACILITY_MANAGER_GROUP_NAME
from logistics_project.apps.registration.validation import intl_clean_phone_number, \
    check_for_dupes
from logistics_project.apps.registration.forms import CommoditiesContactForm
from logistics_project.apps.web_registration.forms import RegisterUserForm, \
    UserSelfRegistrationForm
from logistics.util import config

def _get_program_admin_group():
    return Group.objects.get(name=FACILITY_MANAGER_GROUP_NAME)

class EWSGhanaBasicWebRegistrationForm(RegisterUserForm):
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    organization = forms.CharField(required=False)
    phone = forms.CharField(required=False)
    
    def __init__(self, *args, **kwargs):
        if 'user' in kwargs and kwargs['user'] is not None:
            # display the provided user's information on page load
            user = kwargs['user']
            profile = self.edit_user.get_profile()
            if profile.organization is not None:
                self._add_to_kwargs_initial(kwargs, 'organization', profile.organization)
            if profile.contact and profile.contact.default_connection is not None:
                self._add_to_kwargs_initial(kwargs, 'phone', profile.contact.default_connection.identity)
            if user.first_name is not None:
                self._add_to_kwargs_initial(kwargs, 'first_name', user.first_name)
            if user.last_name is not None:
                self._add_to_kwargs_initial(kwargs, 'last_name', user.last_name)
        return super(EWSGhanaBasicWebRegistrationForm, self).__init__(*args, **kwargs)
    
    def clean_phone(self):
        self.cleaned_data['phone'] = intl_clean_phone_number(self.cleaned_data['phone'])
        check_for_dupes(self.cleaned_data['phone'], self.edit_user.get_profile().contact)
        return self.cleaned_data['phone']

    def save(self, *args, **kwargs):
        user = super(EWSGhanaBasicWebRegistrationForm, self).save(*args, **kwargs)
        profile = user.get_profile()
        if 'organization' in self.cleaned_data:
            profile.organization = self.cleaned_data['organization']
        if 'first_name' in self.cleaned_data:
            user.first_name = self.cleaned_data['first_name']
        if 'last_name' in self.cleaned_data:
            user.last_name = self.cleaned_data['last_name']
        if 'phone' in self.cleaned_data and self.cleaned_data['phone']:
            phone_number = intl_clean_phone_number(self.cleaned_data['phone'])
            profile.get_or_create_contact().set_default_connection_identity(phone_number, backend_name=settings.DEFAULT_BACKEND)
        else:
            contact = profile.contact
            if contact and contact.default_connection:
                contact.default_connection.delete()
        profile.save()
        user.save()
        return user

class EWSGhanaManagerWebRegistrationForm(EWSGhanaBasicWebRegistrationForm): 
    facility = forms.ModelChoiceField(SupplyPoint.objects.all().order_by('name'), 
                                      help_text=('Linking a web user with a facility will allow ', 
                                                 'that user to input stock for that facility from the website.'), 
                                                 required=False)
    is_facility_manager = forms.BooleanField(label='CAN ADD/REMOVE USERS AND FACILITIES', 
                                          help_text='e.g. A DHIO. This includes managing commodities per facility.', 
                                          initial=False, required=False)

    def __init__(self, *args, **kwargs):
        self.edit_user = None
        if 'user' in kwargs and kwargs['user'] is not None:
            self.edit_user = kwargs['user']
            if self.edit_user.groups.filter(name=FACILITY_MANAGER_GROUP_NAME):
                self._add_to_kwargs_initial(kwargs, 'is_facility_manager', True)
        return super(EWSGhanaManagerWebRegistrationForm, self).__init__(*args, **kwargs)

    def save(self, profile_callback=None):
        user = super(EWSGhanaManagerWebRegistrationForm, self).save(profile_callback)
        user.is_staff = False # Can never log into admin site
        pag = _get_program_admin_group()
        if self.cleaned_data['is_facility_manager']:
            user.groups.add(pag)
        elif pag in user.groups.all():
            user.groups.remove(pag)
        user.save()
        return user

class EWSGhanaAdminWebRegistrationForm(EWSGhanaManagerWebRegistrationForm): 
    has_all_permissions = forms.BooleanField(label='GRANT ALL PERMISSIONS', 
                                     help_text='e.g. national administrator. Can add/remove users, facilities, and commodities.', 
                                     initial=False, required=False)

    def __init__(self, *args, **kwargs):
        self.edit_user = None
        if 'user' in kwargs and kwargs['user'] is not None:
            self.edit_user = kwargs['user']
            self._add_to_kwargs_initial(kwargs, 'has_all_permissions', self.edit_user.is_superuser)
        return super(EWSGhanaAdminWebRegistrationForm, self).__init__(*args, **kwargs)

    def save(self, profile_callback=None):
        user = super(EWSGhanaAdminWebRegistrationForm, self).save(profile_callback)
        if self.cleaned_data['has_all_permissions']:
            user.is_superuser = True
        else:
            user.is_superuser = False
        user.save()
        return user

class FacilityForm(forms.ModelForm):
    latitude = forms.DecimalField(required=False)
    longitude = forms.DecimalField(required=False)
    
    class Meta:
        model = SupplyPoint
        exclude = ("last_reported", "groups", "supervised_by")
    
    def __init__(self, *args, **kwargs):
        kwargs['initial'] = {}
        initial_sp = None
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
        if initial_sp:
            self.fields["primary_reporter"].queryset = Contact.objects\
              .filter(supply_point=initial_sp).filter(is_active=True)
        else:
            # if this is a new facility, then no reporters have been defined
            self.fields["primary_reporter"].queryset = Contact.objects.none()
                
    def save(self, *args, **kwargs):
        facility = super(FacilityForm, self).save(*args, **kwargs)
        commodities = Product.objects.filter(is_active=True).order_by('name')
        for commodity in commodities:
            if commodity.sms_code in self.data:
                # this commodity should be stocked
                ps, created = ProductStock.objects.get_or_create(supply_point=facility, 
                                                                 product=commodity)
                ps.is_active = True
                ps.save()
                if facility.primary_reporter and \
                  commodity not in facility.primary_reporter.commodities.all():
                    facility.primary_reporter.commodities.add(commodity)
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
                if facility.primary_reporter and \
                  commodity in facility.primary_reporter.commodities.all():
                    facility.primary_reporter.commodities.remove(commodity)
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

class EWSGhanaSelfRegistrationForm(UserSelfRegistrationForm):
    """
    TODO: merge this into EWSGhanaBasicRegistration form above
    be careful to make sure that the right kind of active/inactive user gets created
    """
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    organization = forms.CharField(required=False)
    phone = forms.CharField(required=False)

    def clean_phone(self):
        self.cleaned_data['phone'] = intl_clean_phone_number(self.cleaned_data['phone'])
        check_for_dupes(self.cleaned_data['phone'])
        return self.cleaned_data['phone']

    def save(self, *args, **kwargs):
        new_user = super(EWSGhanaSelfRegistrationForm, self).save(*args, **kwargs)
        profile = new_user.get_profile()
        if 'designation' in self.cleaned_data and self.cleaned_data['designation']:
            profile = new_user.get_profile()
            profile.designation = self.cleaned_data['designation']
        if 'organization' in self.cleaned_data:
            profile.organization = self.cleaned_data['organization']
        if 'first_name' in self.cleaned_data:
            new_user.first_name = self.cleaned_data['first_name']
        if 'last_name' in self.cleaned_data:
            new_user.last_name = self.cleaned_data['last_name']
        if 'phone' in self.cleaned_data and self.cleaned_data['phone']:
            phone_number = intl_clean_phone_number(self.cleaned_data['phone'])
            profile.get_or_create_contact().set_default_connection_identity(phone_number, backend_name=settings.DEFAULT_BACKEND)
        else:
            contact = profile.contact
            if contact and contact.default_connection:
                contact.default_connection.delete()
        profile.save()
        new_user.save()
        return new_user

class EWSGhanaSMSRegistrationForm(CommoditiesContactForm): 
    """ Slight tweak to the vanilla registration form to automatically
    set the first registered SMS reporter to be the primary reporter
    This is mostly a usability tweak for Ghana. TBD whether it's appropriate elsewhere.
     """
    class Meta:
        model = Contact
        exclude = ("user", "language", "commodities")
    
    def save(self, *args, **kwargs):
        contact = super(EWSGhanaSMSRegistrationForm, self).save(*args, **kwargs)
        responsibilities = []
        if contact and contact.role:
            responsibilities = contact.role.responsibilities.values_list('code', flat=True)
        if contact.supply_point and contact.supply_point.primary_reporter is None and \
          config.Responsibilities.STOCK_ON_HAND_RESPONSIBILITY in responsibilities:
            contact.supply_point.primary_reporter = contact
            contact.supply_point.save()
        return contact


