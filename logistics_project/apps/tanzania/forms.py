from django import forms
from logistics_project.apps.tanzania.models import AdHocReport
from logistics.models import SupplyPoint
from logistics_project.apps.tanzania.config import SupplyPointCodes


class AdHocReportForm(forms.ModelForm):
    supply_point = forms.ModelChoiceField(queryset=SupplyPoint.objects.filter\
                                          (type__code=SupplyPointCodes.DISTRICT))
    class Meta:
        model = AdHocReport