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
from logistics.models import Product, SupplyPoint, ProductStock, ProductType
from logistics_project.apps.ewsghana import loader
from logistics_project.apps.ewsghana.models import GhanaFacility
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
    designation = forms.CharField(required=True)
    organization = forms.CharField(required=True)
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    phone = forms.CharField(required=False)
    program = forms.ModelChoiceField(ProductType.objects.all().order_by('name'), 
                                     required=False)
    sms_notifications = forms.BooleanField(required=False, initial=True)
    
    def __init__(self, *args, **kwargs):
        if 'user' in kwargs and kwargs['user'] is not None:
            # display the provided user's information on page load
            self.edit_user = kwargs['user']
            profile = self.edit_user.get_profile()
            if profile.organization is not None:
                self._add_to_kwargs_initial(kwargs, 'organization', profile.organization)
            if profile.program is not None:
                self._add_to_kwargs_initial(kwargs, 'program', profile.program)
            if profile.contact and profile.contact.default_connection is not None:
                self._add_to_kwargs_initial(kwargs, 'phone', profile.contact.default_connection.identity)
            if self.edit_user.first_name is not None:
                self._add_to_kwargs_initial(kwargs, 'first_name', self.edit_user.first_name)
            if self.edit_user.last_name is not None:
                self._add_to_kwargs_initial(kwargs, 'last_name', self.edit_user.last_name)
            self._add_to_kwargs_initial(kwargs, 'sms_notifications', profile.sms_notifications)
        return super(EWSGhanaBasicWebRegistrationForm, self).__init__(*args, **kwargs)
    
    def clean_phone(self):
        self.cleaned_data['phone'] = intl_clean_phone_number(self.cleaned_data['phone'])
        if self.edit_user and self.edit_user.get_profile():
            check_for_dupes(self.cleaned_data['phone'], self.edit_user.get_profile().contact)
        else: 
            check_for_dupes(self.cleaned_data['phone'])
        return self.cleaned_data['phone']

    def save(self, *args, **kwargs):
        user = super(EWSGhanaBasicWebRegistrationForm, self).save(*args, **kwargs)
        profile = user.get_profile()
        if 'organization' in self.cleaned_data:
            profile.organization = self.cleaned_data['organization']
        if 'program' in self.cleaned_data:
            profile.program = self.cleaned_data['program']
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
        profile.sms_notifications = self.cleaned_data.get('sms_notifications', True)
        profile.save()
        user.save()
        return user

class EWSGhanaManagerWebRegistrationForm(EWSGhanaBasicWebRegistrationForm): 
    facility = forms.ModelChoiceField(SupplyPoint.objects.all().order_by('name'), 
                                      help_text=('Linking a web user with a facility will allow ', 
                                                 'that user to input stock for that facility from the website.'), 
                                                 required=False)
    is_facility_manager = forms.BooleanField(label='CAN ADD/REMOVE USERS AND FACILITIES', 
                                          help_text='e.g. DHIO, RHIO. This includes managing commodities per facility.', 
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
    parent_location = forms.ModelChoiceField(Location.objects.exclude(type__slug=config.LocationCodes.FACILITY).order_by('name'), 
                                             required=True)
    
    class Meta:
        model = GhanaFacility
        exclude = ("last_reported", "groups", "supervised_by", "location")
    
    def __init__(self, *args, **kwargs):
        kwargs['initial'] = {}
        initial_sp = None
        if 'instance' in kwargs and kwargs['instance']:
            initial_sp = kwargs['instance']
            if 'initial' not in kwargs:
                kwargs['initial'] = {}
            pss = ProductStock.objects.filter(supply_point=initial_sp, 
                                              is_active=True, 
                                              product__is_active=True)
            kwargs['initial']['commodities'] = [p.product.pk for p in pss]
            if initial_sp.location:
                kwargs['initial']['parent_location'] = initial_sp.location.tree_parent
                if initial_sp.location.point:
                    kwargs['initial']['latitude'] = initial_sp.location.point.latitude
                    kwargs['initial']['longitude'] = initial_sp.location.point.longitude
        super(FacilityForm, self).__init__(*args, **kwargs)
        if initial_sp:
            self.fields["primary_reporter"].queryset = Contact.objects\
              .filter(supply_point=initial_sp).filter(is_active=True)
        else:
            # if this is a new facility, then no reporters have been defined
            self.fields["primary_reporter"].queryset = Contact.objects.none()
        # it will be more user-friendly in the long run to hide facility locations from this list,
        # once we've turned facility into a subclass of location...
        #removing this for now - since it'll break pre-existing saved facilities
        # self.fields['location'].queryset = Location.objects.exclude(type__slug=config.LocationCodes.FACILITY)
        #self.fields['location'].queryset = Location.objects.exclude(type__slug=config.LocationCodes.FACILITY)
				
    def save(self, *args, **kwargs):
        facility = super(FacilityForm, self).save(commit=False, *args, **kwargs)
        if self.cleaned_data['parent_location']:
            def _create_new_fac_location(fac, parent):
                loc, created = loader._get_or_create_location(fac.name, 
                                                              parent)
                fac.location = loc
            try:
                previous_instance = GhanaFacility.objects.get(code=self.instance.code)
            except GhanaFacility.DoesNotExist:
                _create_new_fac_location(facility, self.cleaned_data['parent_location'])
            else:
                if facility.location.tree_parent and \
                  facility.location.tree_parent != self.cleaned_data['parent_location']:
                    if facility.location.name == facility.name:
                        facility.location.set_parent(self.cleaned_data['parent_location'])
                    else:
                        _create_new_fac_location(facility, self.cleaned_data['parent_location'])
        facility.save()
        commodities = Product.objects.filter(is_active=True).order_by('name')
        for commodity in commodities:
            if commodity.sms_code in self.data:
                facility.activate_product(commodity)
            else:
                facility.deactivate_product(commodity)
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
    program = forms.ModelChoiceField(ProductType.objects.all().order_by('name'), 
                                     required=False)
    sms_notifications = forms.BooleanField(required=False, initial=True)

    def clean_phone(self):
        self.cleaned_data['phone'] = intl_clean_phone_number(self.cleaned_data['phone'])
        check_for_dupes(self.cleaned_data['phone'])
        return self.cleaned_data['phone']

    def save(self, *args, **kwargs):
        new_user = super(EWSGhanaSelfRegistrationForm, self).save(*args, **kwargs)
        profile = new_user.get_profile()
        if 'designation' in self.cleaned_data and self.cleaned_data['designation']:
            profile.designation = self.cleaned_data['designation']
        if 'program' in self.cleaned_data and self.cleaned_data['program']:
            profile.program = self.cleaned_data['program']
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
        profile.sms_notifications = self.cleaned_data.get('sms_notifications', True)
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
    
    def __init__(self, *args, **kwargs):
        super(EWSGhanaSMSRegistrationForm, self).__init__(*args, **kwargs)
        self.fields['name'].label = "First Name"
        
    def save(self, *args, **kwargs):
        contact = super(EWSGhanaSMSRegistrationForm, self).save(*args, **kwargs)
        if contact.supply_point:
            contact.supply_point.add_contact(contact)
        return contact


