from django import forms
from logistics_project.apps.tanzania.models import AdHocReport
from logistics.models import SupplyPoint
from logistics_project.apps.tanzania.config import SupplyPointCodes
from django.forms.fields import EmailField
from django.core.validators import EmailValidator, validate_email
from django.utils.translation import ugettext as _
from rapidsms.contrib.locations.models import Location

class AdHocReportForm(forms.ModelForm):
    supply_point = forms.ModelChoiceField(queryset=SupplyPoint.objects.filter\
                                          (type__code__in=[SupplyPointCodes.DISTRICT,
                                                           SupplyPointCodes.REGION]))

    def clean_recipients(self):
        data = self.cleaned_data['recipients']
        recipients = data.split(",")
        for email in recipients:
            validate_email(email.strip())
        return data

    class Meta:
        model = AdHocReport


class UploadFacilityFileForm(forms.Form):
    file = forms.FileField()


class SupervisionDocumentForm(forms.Form):
    document = forms.FileField(
        label=_('Upload a file'),
    )


class SMSFacilityForm(forms.Form):
    choices = [
        ['', _('Select a type')],
        ['groups', _('Reporting groups')],
        ['regions', _('Regions')],
        ['districts', _('Districts')],
        ['facilities', _('Facilities')],
    ]
    recipient_select_type = forms.ChoiceField(choices=choices)

    group_a = forms.BooleanField(label=_('Reporting group A'), required=False)
    group_b = forms.BooleanField(label=_('Reporting group B'), required=False)
    group_c = forms.BooleanField(label=_('Reporting group C'), required=False)

    regions = forms.ModelMultipleChoiceField(
        Location.objects.filter(type__name='REGION'),
        label=_('Regions'),
        required=False,
    )

    districts = forms.ModelMultipleChoiceField(
        Location.objects.filter(type__name='DISTRICT'),
        label=_('Districts'),
        required=False,
    )

    facility_district = forms.ModelChoiceField(
        Location.objects.filter(type__name='DISTRICT'),
        label=_('First select a district'),
        required=False,
    )
    facilities = forms.MultipleChoiceField(
        label=_('Facilities'),
        required=False,
    )

    message = forms.CharField(
        label=_('Message'),
        widget=forms.Textarea,
    )
