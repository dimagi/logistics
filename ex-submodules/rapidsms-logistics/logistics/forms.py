#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django import forms
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.db.models import Q
from django.utils.translation import ugettext as _
from rapidsms.models import Backend, Connection, Contact
from logistics.apps.logistics.models import ContactRole, Product

class ContactForm(forms.ModelForm):
    name = forms.CharField()
    phone = forms.CharField()

    class Meta:
        model = Contact
        exclude = ("user",)

    def __init__(self, **kwargs):
        super(ContactForm, self).__init__(**kwargs)
        self.fields['role'].label = _("Role")
        self.fields['name'].label = _("Name")
        self.fields['phone'].label = _("Phone")
        self.fields['phone'].help_text = _("Enter the fully qualified number.<br/>Example: 0012121234567")

        if kwargs.has_key('instance'):
            if kwargs['instance']:
                instance = kwargs['instance']
                self.initial['phone'] = instance.phone

    def clean_phone(self):
        model = super(ContactForm, self).save(commit=False)
        self.cleaned_data['phone'] = self._clean_phone_number(self.cleaned_data['phone'])
        dupes = Connection.objects.filter(identity=self.cleaned_data['phone'])
        dupe_count = dupes.count()
        if dupe_count > 1:
            raise forms.ValidationError("Phone number already registered!")
        if dupe_count == 1:
            # could be that we are editing an existing model
            if dupes[0].contact.name != self.cleaned_data['name']:
                raise forms.ValidationError("Phone number already registered!")
        return self.cleaned_data['phone']

    def _clean_phone_number(self, phone_number):
        """
        TODO: define the number cleaning function as appropriate for whatever country/gateway you're using

        """
        raise NotImplementedError()

    def save(self, commit=True):
        model = super(ContactForm, self).save(commit=False)
        if commit:
            model.save()
            conn = model.default_connection
            if not conn:
                if settings.DEFAULT_BACKEND:
                    backend = Backend.objects.get(name=settings.DEFAULT_BACKEND)
                else:
                    backend = Backend.objects.all()[0]
                conn = Connection(backend=backend,
                                  contact=model)
            conn.identity = self.cleaned_data['phone']
            conn.save()
        return model

class IntlSMSContactForm(ContactForm):
    def __init__(self, **kwargs):
        super(IntlSMSContactForm, self).__init__(**kwargs)
        self.fields['phone'].help_text = _("Enter the fully qualified number.<br/>" + \
                                           "Example: %(i)s%(c)s2121234567" % \
                                           {'i':settings.INTL_DIALLING_CODE,
                                            'c':settings.COUNTRY_CODE})

    def _clean_phone_number(self, phone_number):
        """
        * remove junk characters
        * replaces optional domestic dialling code with intl dialling code
        * prefix with international dialling code (specified in settings.py)
        """
        cleaned = phone_number.strip()
        junk = [',', '-', ' ', '(', ')']
        for mark in junk:
            cleaned = cleaned.replace(mark, '')

        # replace domestic with intl dialling code, if domestic code defined
        idc = "%s%s" % (settings.INTL_DIALLING_CODE, settings.COUNTRY_CODE)
        try:
            ddc = str(settings.DOMESTIC_DIALLING_CODE)
            if cleaned.startswith(ddc):
                cleaned = "%s%s" % (idc, cleaned.lstrip(ddc))
                return cleaned
        except NameError:
            # ddc not defined, no biggie
            pass
        if cleaned.isdigit():
            return cleaned
        if cleaned.startswith(idc):
            return cleaned
        raise forms.ValidationError("Poorly formatted phone number. " + \
                                    "Please enter the fully qualified number." + \
                                    "Example: %(intl)s2121234567" % \
                                    {'intl':idc})

