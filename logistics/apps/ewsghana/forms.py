""" 
import RegistrationForm from the django_registraton 3rd party app 

This is a little non-DRY with respect to ModelForm functionality
since the 3rd party register app didn't use ModelForm properly
"""
from datetime import datetime
from django import forms
from django.contrib.auth.models import Group
from rapidsms.contrib.locations.models import Location
from logistics.apps.web_registration.forms import AdminRegistersUserForm

PROGRAM_ADMIN_GROUP_NAME = 'program_admin'
def _get_program_admin_group():
    return Group.objects.get(name=PROGRAM_ADMIN_GROUP_NAME)

class EWSGhanaWebRegistrationForm(AdminRegistersUserForm): 
    is_program_admin = forms.BooleanField(label='User is a health administrator', initial=False, required=False)
    is_IT_admin = forms.BooleanField(label='User is an IT administrator', initial=False, required=False)
    
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
        return super(EWSGhanaWebRegistrationForm, self).__init__(*args, **kwargs)

    def save(self, profile_callback=None):
        user = super(EWSGhanaWebRegistrationForm, self).save(profile_callback)
        user.is_staff = False # Can never log into admin site
        if self.cleaned_data['is_program_admin']:
            user.groups.add(_get_program_admin_group())
        if self.cleaned_data['is_IT_admin']:
            user.is_superuser = True
        user.save()
        return user

