""" 
import RegistrationForm from the django_registraton 3rd party app 

This is a little non-DRY with respect to ModelForm functionality
since the 3rd party register app didn't use ModelForm properly
"""
from datetime import datetime
from django import forms
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from registration.forms import RegistrationForm
from registration.models import RegistrationProfile
from rapidsms.contrib.locations.models import Location
from logistics.apps.logistics.models import SupplyPoint

class AdminRegistersUserForm(RegistrationForm): 
    location = forms.ModelChoiceField(Location.objects.all().order_by('name'), required=False)
    facility = forms.ModelChoiceField(SupplyPoint.objects.all().order_by('name'), required=False)
    password1 = forms.CharField(widget=forms.PasswordInput(attrs=None, render_value=False),
                                label=_(u'password'), required=False)
    password2 = forms.CharField(widget=forms.PasswordInput(attrs=None, render_value=False),
                                label=_(u'password (again)'), required=False)
    
    def __init__(self, *args, **kwargs):
        self.edit_user = None
        if 'user' in kwargs and kwargs['user'] is not None:
            self.edit_user = kwargs['user']
            initial = {}
            if 'initial' in kwargs:
                initial = kwargs['initial']
            initial['username'] = self.edit_user.username
            initial['email'] = self.edit_user.email
            profile = self.edit_user.get_profile()
            if profile.location is not None:
                initial['location'] = profile.location.pk
            if profile.supply_point is not None:
                initial['facility'] = profile.supply_point.pk
            kwargs['initial'] = initial
        if 'user' in kwargs:
            kwargs.pop('user')
        return super(AdminRegistersUserForm, self).__init__(*args, **kwargs)
        
    def clean_username(self):
        """
        Validate that the username is alphanumeric and is not already
        in use.
        
        """
        if self.edit_user is None:
            # checks for alnum and that this user doesn't already exist
            return super(AdminRegistersUserForm, self).clean_username()
        # just checks for alnum
        if not self.cleaned_data['username'].isalnum():
            raise forms.ValidationError(_(u'Please enter a username containing only letters and numbers.'))
        return self.cleaned_data['username']

    def clean(self):
        """
        Verifiy that new users are created with passwords
        For existing users, we don't need to supply a password
        
        """
        if self.edit_user is None and len(self.cleaned_data['password1']) == 0:
            raise forms.ValidationError(_(u'You must supply a password when creating a user'))
        return super(AdminRegistersUserForm, self).clean()

    def save(self, profile_callback=None):
        if self.edit_user is None:
            # creates user and profile object
            user = RegistrationProfile.objects.create_inactive_user(username=self.cleaned_data['username'],
                                                                    password=self.cleaned_data['password1'],
                                                                    email=self.cleaned_data['email'], 
                                                                    send_email=False,
                                                                    profile_callback=profile_callback)
            user.last_login =  datetime(1970,1,1)
            # date_joined is used to determine expiration of the invitation key - I'd like to
            # munge it back to 1970, but can't because it makes all keys look expired.
            user.date_joined = datetime.utcnow()
        else:
            # skips creating and just updates the relevant fields
            self.edit_user.username = self.cleaned_data['username']
            if len(self.cleaned_data['password1']) > 0:
                self.edit_user.set_password(self.cleaned_data['password1'])
            self.edit_user.email = self.cleaned_data['email']
            user = self.edit_user
        user.is_active = True
        user.is_staff = False # Can never log into admin site
        user.save()
        if 'location' in self.cleaned_data or 'facility' in self.cleaned_data:
            profile = user.get_profile()
            profile.location = self.cleaned_data['location']
            profile.supply_point = self.cleaned_data['facility']
            profile.save()
        return user

class AdminRegistersUserFormActiveAdmin(AdminRegistersUserForm): 
    # set the is_active flag, as well as permissions
    is_active = forms.BooleanField(label='User is active (can login)', initial=True, required=False)
    is_admin = forms.BooleanField(label='User is an administrator', initial=False, required=False)
    
    def __init__(self, *args, **kwargs):
        self.edit_user = None
        if 'user' in kwargs and kwargs['user'] is not None:
            self.edit_user = kwargs['user']
            initial = {}
            if 'initial' in kwargs:
                initial = kwargs['initial']
            initial['is_active'] = self.edit_user.is_active
            initial['is_admin'] = self.edit_user.is_superuser
            kwargs['initial'] = initial
        return super(AdminRegistersUserFormActiveAdmin, self).__init__(*args, **kwargs)

    def save(self, profile_callback=None):
        user = super(AdminRegistersUserFormActiveAdmin, self).save(profile_callback)
        user.is_staff = False # Can never log into admin site
        user.is_active = self.cleaned_data['is_active']
        if user.supply_point:
            user.supply_point.active = user.is_active # deactivate supply point if user is deactivated and vice versa
            user.supply_point.save()
        user.is_superuser = self.cleaned_data['is_admin']   
        user.save()
        return user

