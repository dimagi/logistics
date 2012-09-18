from django import forms
from logistics_project.apps.tanzania.models import AdHocReport
from logistics.models import SupplyPoint
from logistics_project.apps.tanzania.config import SupplyPointCodes
from django.forms.fields import EmailField
from django.core.validators import EmailValidator, validate_email


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
    file  = forms.FileField()
    