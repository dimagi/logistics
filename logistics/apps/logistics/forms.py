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

        if kwargs.has_key('instance'):
            if kwargs['instance']:
                instance = kwargs['instance']
                self.initial['phone'] = instance.phone

    def clean_phone(self):
        model = super(ContactForm, self).save(commit=False)
        dupes = Connection.objects.filter(identity=self.cleaned_data['phone'])
        dupe_count = dupes.count()
        if dupe_count > 1:
            raise forms.ValidationError("Phone number already registered!")
        if dupe_count == 1:
            # could be that we are editing an existing model
            if dupes[0].contact.name != self.cleaned_data['name']:
                raise forms.ValidationError("Phone number already registered!")
        return self.cleaned_data['phone']

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
