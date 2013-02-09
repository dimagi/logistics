#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8
from __future__ import absolute_import
from django import forms
from django.contrib.sites.models import Site
from django.db import transaction
from django.utils.translation import ugettext as _
from rapidsms.conf import settings
from rapidsms.models import Backend, Connection, Contact
from logistics.models import SupplyPoint, Product
from logistics_project.apps.registration.validation import check_for_dupes, intl_clean_phone_number

# the built-in FileField doesn't specify the 'size' attribute, so the
# widget is rendered at its default width -- which is too wide for our
# form. this is a little hack to shrink the field.
class SmallFileField(forms.FileField):
    def widget_attrs(self, widget):
        return { "size": 10 }


class BulkRegistrationForm(forms.Form):
    bulk = SmallFileField(
        label="Upload CSV file",
        required=False,
        help_text="Upload a <em>plain text file</em> " +
                  "containing a single contact per line, for example: <br/>" +
                  "<em>firstname lastname, backend_name, identity</em>")


class ContactForm(forms.ModelForm):
    name = forms.CharField()
    phone = forms.CharField()

    class Meta:
        model = Contact
        exclude = ("user", "_default_connection")

    def __init__(self, *args, **kwargs):
        super(ContactForm, self).__init__(*args, **kwargs)
        self.fields['role'].label = _("Role")
        self.fields['name'].label = _("Name")
        self.fields['phone'].label = _("Phone")
        self.fields['phone'].help_text = _("Enter the fully qualified number.<br/>Example: 0012121234567")
        
        if kwargs.has_key('instance'):
            if kwargs['instance']:
                instance = kwargs['instance']
                self.initial['phone'] = instance.phone
    
    def clean_phone(self):
        return self._clean_phone_and_check_dupes(self.cleaned_data['phone'])

    def _clean_phone_and_check_dupes(self, phone_number):
        phone_number = self._clean_phone_number(phone_number)
        if self.instance:
            check_for_dupes(phone_number, contact=self.instance)
        else:
            check_for_dupes(phone_number)
        return phone_number
    
    def _clean_phone_number(self, phone_number):
        """
        TODO: define the number cleaning function as appropriate for whatever country/gateway you're using

        """
        raise NotImplementedError()

    @transaction.commit_on_success
    def save(self, commit=True):
        model = super(ContactForm, self).save(commit=False)
        if commit:
            model.save()
            model.set_default_connection_identity(self.cleaned_data['phone'], 
                                                  backend_name=settings.DEFAULT_BACKEND)
        return model

class IntlSMSContactForm(ContactForm):
    def __init__(self, *args, **kwargs):
        super(IntlSMSContactForm, self).__init__(*args, **kwargs)
        self.fields['phone'].help_text = _("Enter the fully qualified number.<br/>" + \
                                           "Example: %(i)s%(c)s2121234567" % \
                                           {'i':settings.INTL_DIALLING_CODE,
                                            'c':settings.COUNTRY_DIALLING_CODE})

    def _clean_phone_number(self, phone_number):
        return intl_clean_phone_number(phone_number)

class CommoditiesContactForm(IntlSMSContactForm):
    supply_point = forms.ModelChoiceField(SupplyPoint.objects.filter(active=True).order_by('name'),
                                          required=False,  
                                          label='Facility')

    class Meta:
        model = Contact
        exclude = ("user", "language", "_default_connection")

    def __init__(self, *args , **kwargs):
        super(CommoditiesContactForm, self ).__init__(*args,**kwargs)
        if 'commodities' in self.fields:
            self.fields['commodities'].queryset = Product.objects.filter(is_active=True)
    
    @transaction.commit_on_success
    def save(self, commit=True):
        model = super(CommoditiesContactForm, self).save(commit=False)
        if commit:
            model.save()
            model.default_connection = self.cleaned_data['phone']
            self.save_m2m()
        return model
