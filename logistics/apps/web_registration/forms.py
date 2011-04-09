# import RegistrationForm from the django_registraton 3rd party app
from registration.forms import RegistrationForm
from django import forms
from rapidsms.contrib.locations.models import Location
from logistics.apps.logistics.models import Facility

class AdminRegistersUserForm(RegistrationForm): 
    # Need the is_active flag, as well as permissions.
    is_active = forms.BooleanField(label='User is active (can login)', initial=True, required=False)
    is_admin = forms.BooleanField(label='User is an administrator', initial=False, required=False)
    location = forms.ModelChoiceField(Location.objects.all().order_by('name'), required=False)
    # TODO filter down facilities by location in javascript
    facility = forms.ModelChoiceField(Facility.objects.all().order_by('name'), required=False)
