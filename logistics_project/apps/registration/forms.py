#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from django import forms
from django.conf import settings
from django.contrib.sites.models import Site
from django.db import transaction
from django.utils.translation import ugettext as _
from rapidsms.models import Backend, Connection, Contact
from logistics.models import SupplyPoint, ContactRole, Product
from static.malawi.config import Roles, SupplyPointCodes, BaseLevel


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
        exclude = ("user", )

    def __init__(self, **kwargs):
        super(ContactForm, self).__init__(**kwargs)
        self.fields['role'].label = _("Role")
        self.fields['role'].choices = self.get_role_choices()
        self.fields['name'].label = _("Name")
        self.fields['phone'].label = _("Phone")
        self.fields['phone'].help_text = _("Enter the fully qualified number.<br/>Example: 0012121234567")

        if kwargs.has_key('instance'):
            if kwargs['instance']:
                instance = kwargs['instance']
                self.initial['phone'] = instance.phone

    def get_role_choices(self):
        role_choices = [('', '---------')]
        facility_roles = []
        district_roles = []
        zone_roles = []

        for role in ContactRole.objects.all():
            if role.code == Roles.HSA:
                role_choices.append((role.pk, "HSA"))
            elif role.code in Roles.FACILITY_ONLY:
                facility_roles.append((role.pk, "Facility User - " + role.name))
            elif role.code in Roles.DISTRICT_ONLY:
                district_roles.append((role.pk, "District User - " + role.name))
            elif role.code in Roles.ZONE_ONLY:
                zone_roles.append((role.pk, "Zone User - " + role.name))
            else:
                role_choices.append((role.pk, role.name))

        role_choices.extend(facility_roles)
        role_choices.extend(district_roles)
        role_choices.extend(zone_roles)
        return role_choices

    def clean_phone(self):
        self.cleaned_data['phone'] = self._clean_phone_number(self.cleaned_data['phone'])
        if settings.DEFAULT_BACKEND:
            backend = Backend.objects.get(name=settings.DEFAULT_BACKEND)
        else:
            backend = Backend.objects.all()[0]
        dupes = Connection.objects.filter(identity=self.cleaned_data['phone'], 
                                          backend=backend)
        dupe_count = dupes.count()
        if dupe_count > 1:
            raise forms.ValidationError("Phone number already registered!")
        if dupe_count == 1:
            if dupes[0].contact is None:
                # this is fine, it just means we have a dangling connection
                # which we'll steal when we save
                pass
            # could be that we are editing an existing model
            elif dupes[0].contact != self.instance:
                raise forms.ValidationError("Phone number already registered!")
        return self.cleaned_data['phone']

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
            conn = model.default_connection
            if not conn:
                if settings.DEFAULT_BACKEND:
                    backend = Backend.objects.get(name=settings.DEFAULT_BACKEND)
                else:
                    backend = Backend.objects.all()[0]
                try:
                    conn = Connection.objects.get(backend=backend, 
                                                  identity=self.cleaned_data['phone'])
                except Connection.DoesNotExist:
                    # good, it doesn't exist already
                    conn = Connection(backend=backend,
                                      contact=model)
                else: 
                    # this connection already exists. just steal it. 
                    conn.contact = model
            conn.identity = self.cleaned_data['phone']
            conn.save()
        return model

class IntlSMSContactForm(ContactForm):
    def __init__(self, **kwargs):
        super(IntlSMSContactForm, self).__init__(**kwargs)
        self.fields['phone'].help_text = _("Enter the fully qualified number.<br/>" + \
                                           "Example: %(i)s%(c)s2121234567" % \
                                           {'i':settings.INTL_DIALLING_CODE,
                                            'c':settings.COUNTRY_DIALLING_CODE})

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
        idc = "%s%s" % (settings.INTL_DIALLING_CODE, settings.COUNTRY_DIALLING_CODE)
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

class CommoditiesContactForm(IntlSMSContactForm):
    supply_point = forms.ModelChoiceField(SupplyPoint.objects.all().order_by('name'),
                                          required=False,  
                                          label='Location')

    # Only expose HSA-level products in the managed commodity picker.
    # Facility users automatically manage all Facility-level products.
    # This input is disabled for all contacts except for HSAs in templates/registration/dashboard.html
    commodities = forms.ModelMultipleChoiceField(
        queryset=Product.objects.filter(type__base_level=BaseLevel.HSA, is_active=True),
        required=False,
        help_text='User manages these commodities. Hold down "Control", or "Command" on a Mac, to select more than one.'
    )

    class Meta:
        model = Contact
        exclude = ("user", "language")

    def clean_supply_point(self):
        supply_point = self.cleaned_data.get('supply_point')
        if not supply_point:
            return None

        role = self.cleaned_data.get('role')
        if not role:
            return supply_point

        if role.code == Roles.HSA and supply_point.type.code != SupplyPointCodes.HSA:
            raise forms.ValidationError("There is a mismatch between role and location. "
                "You have chosen an HSA role but a non-HSA location.")
        elif role.code in Roles.FACILITY_ONLY and supply_point.type.code != SupplyPointCodes.FACILITY:
            raise forms.ValidationError("There is a mismatch between role and location. "
                "You have chosen a facility role but a non-facility location.")
        elif role.code in Roles.DISTRICT_ONLY and supply_point.type.code != SupplyPointCodes.DISTRICT:
            raise forms.ValidationError("There is a mismatch between role and location. "
                "You have chosen a district role but a non-district location.")
        elif role.code in Roles.ZONE_ONLY and supply_point.type.code != SupplyPointCodes.ZONE:
            raise forms.ValidationError("There is a mismatch between role and location. "
                "You have chosen a zone role but not a zone location.")

        return supply_point

    @transaction.commit_on_success
    def save(self, commit=True):
        model = super(CommoditiesContactForm, self).save(commit=False)
        if commit:
            model.save()
            model.default_connection = self.cleaned_data['phone']
            self.save_m2m()
        return model
