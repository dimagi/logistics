# import RegistrationForm from the django_registraton 3rd party app
from registration.forms import RegistrationForm
from django import forms

class AdminRegistersUserForm(RegistrationForm): 
    # Need the is_active flag, as well as permissions.
    is_active = forms.BooleanField(label='User is active (can login)', initial=True, required=False)
    is_admin = forms.BooleanField(label='User is an administrator', initial=False, required=False)
