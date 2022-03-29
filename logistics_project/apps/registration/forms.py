from __future__ import absolute_import
from __future__ import unicode_literals
from builtins import object
from django import forms
from django.db import transaction
from rapidsms.models import Backend, Connection, Contact
from logistics.models import SupplyPoint, ContactRole, Product
from logistics_project.apps.malawi.util import get_backend_name_for_phone_number
from static.malawi.config import Roles, SupplyPointCodes, BaseLevel


# the built-in FileField doesn't specify the 'size' attribute, so the
# widget is rendered at its default width -- which is too wide for our
# form. this is a little hack to shrink the field.
class SmallFileField(forms.FileField):
    def widget_attrs(self, widget):
        return { "size": 10 }


class ContactForm(forms.ModelForm):
    phone = forms.CharField(
        help_text = "Enter 12-digit international number<br/>Example: +265123456789",
    )

    supply_point = forms.ModelChoiceField(
        SupplyPoint.objects.all().order_by('name'),
        required=False,
        label='Location'
    )

    # Only expose HSA-level products in the managed commodity picker.
    # Facility users automatically manage all Facility-level products.
    # This input is disabled for all contacts except for HSAs in templates/registration/dashboard.html
    commodities = forms.ModelMultipleChoiceField(
        queryset=Product.objects.filter(type__base_level=BaseLevel.HSA, is_active=True),
        required=False,
        help_text='User manages these commodities. Hold down "Control", or "Command" on a Mac, to select more than one.'
    )

    class Meta(object):
        model = Contact
        exclude = ('user', 'language')

    def __init__(self, **kwargs):
        super(ContactForm, self).__init__(**kwargs)
        self.fields['role'].choices = self.get_role_choices()

        instance = kwargs.get('instance')
        if instance:
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

    def get_connection(self, phone_number, backend_name):
        try:
            return Connection.objects.get(identity=phone_number, backend__name=backend_name)
        except Connection.DoesNotExist:
            return None

    def get_connection_for_contact(self, contact):
        try:
            return Connection.objects.get(contact=contact)
        except Connection.DoesNotExist:
            return None
        except Connection.MultipleObjectsReturned:
            # We only expect 1 Connection per Contact
            raise

    def clean_phone(self):
        country_prefix = '+265'
        error_message = "Enter 12-digit international number. Example: +265123456789"

        phone_number = self.cleaned_data['phone'].strip()
        if phone_number.startswith('0'):
            phone_number = country_prefix + phone_number[1:]

        if not phone_number.startswith('+'):
            phone_number = '+' + phone_number

        if not phone_number.startswith(country_prefix):
            raise forms.ValidationError(error_message)

        if len(phone_number) != 13:
            raise forms.ValidationError(error_message)

        backend_name = get_backend_name_for_phone_number(phone_number)
        existing_connection = self.get_connection(phone_number, backend_name)

        if (
            existing_connection and
            existing_connection.contact is not None
            and existing_connection.contact != self.instance
        ):
            raise forms.ValidationError("Phone number is already registered to another contact.")

        return phone_number

    @transaction.atomic
    def save(self):
        model = super(ContactForm, self).save(commit=True)

        phone_number = self.cleaned_data['phone']
        backend_name = get_backend_name_for_phone_number(phone_number)
        connection = self.get_connection_for_contact(model)

        connection_is_up_to_date = (
            connection is not None and
            connection.identity == phone_number and
            connection.backend.name == backend_name
        )

        if not connection_is_up_to_date:
            if connection:
                # The phone number changed, so unassign the old connection, and create a new one.
                # This preserves accuracy of the message log history.
                connection.contact = None
                connection.save()

            existing_connection = self.get_connection(phone_number, backend_name)
            if existing_connection:
                if existing_connection.contact is None:
                    existing_connection.contact = model
                    existing_connection.save()
                else:
                    # This should not happen based on our validation
                    raise RuntimeError("Phone number is already in use")
            else:
                Connection.objects.create(
                    contact=model,
                    identity=phone_number,
                    backend=Backend.objects.get(name=backend_name),
                )

        return model

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
