from django import forms
from logistics_project.apps.malawi.models import Organization
from logistics.models import SupplyPoint
from logistics.util import config

class OrganizationForm(forms.ModelForm):
    name = forms.CharField()
    managed_supply_points = forms.ModelMultipleChoiceField(
        queryset=SupplyPoint.objects.filter(active=True,
                                   type__code=config.SupplyPointCodes.DISTRICT),
        required=False                                               
    )
    class Meta:
        model = Organization
        