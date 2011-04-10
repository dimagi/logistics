""" import RegistrationForm from the django_registraton 3rd party app """
from django import forms
from django.contrib.auth.models import User
from registration.forms import RegistrationForm
from rapidsms.contrib.locations.models import Location
from logistics.apps.logistics.models import Facility

class AdminRegistersUserForm(RegistrationForm): 
    # Need the is_active flag, as well as permissions.
    is_active = forms.BooleanField(label='User is active (can login)', initial=True, required=False)
    is_admin = forms.BooleanField(label='User is an administrator', initial=False, required=False)
    location = forms.ModelChoiceField(Location.objects.all().order_by('name'), required=False)
    # TODO filter down facilities by location in javascript
    facility = forms.ModelChoiceField(Facility.objects.all().order_by('name'), required=False)

class AdminEditUserForm(AdminRegistersUserForm): 
    def clean_username(self):
        """
        Validate that the username is alphanumeric and is not already
        in use.
        
        """
        try:
            User.objects.get(username__iexact=self.cleaned_data['username'])
        except User.DoesNotExist:
            raise forms.ValidationError(_(u'This user has not been registered.'))
        return self.cleaned_data['username']

    def save(self, profile_callback=None):
        return User.objects.get(username=self.cleaned_data['username'])
