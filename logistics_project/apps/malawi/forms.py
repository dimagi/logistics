from django import forms
from logistics_project.apps.malawi.models import Organization

class OrganizationForm(forms.ModelForm):
    name = forms.CharField()
    
    class Meta:
        model = Organization
        