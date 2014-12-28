from django import forms
from django.contrib.auth.models import Group, User

from logistics.util import config
from logistics.models import SupplyPoint, Product, LogisticsProfile

from logistics_project.apps.malawi.models import Organization


class OrganizationForm(forms.ModelForm):
    name = forms.CharField()
    managed_supply_points = forms.ModelMultipleChoiceField(
        queryset=SupplyPoint.objects.filter(active=True,
            type__code=config.SupplyPointCodes.DISTRICT),
        required=False
    )

    class Meta:
        model = Organization
        

class LogisticsProfileForm(forms.ModelForm):
    supply_point = forms.ModelChoiceField(
        queryset=SupplyPoint.objects.filter(active=True,
            type__code=config.SupplyPointCodes.DISTRICT),
        required=False,
        label='District'
    )

    def __init__(self, *args, **kwargs):
        super(LogisticsProfileForm, self).__init__(*args, **kwargs)
        self.fields['groups'] = self.get_group_field()

    def get_group_field(self):
        groups = forms.ModelMultipleChoiceField(
            queryset=Group.objects.all(),
            required=False,
            initial=[g.id for g in self.instance.user.groups.all()],
            label='Groups'
        )
        return groups

    def clean(data):
        user = data.instance.user
        for group in Group.objects.all():
            group.user_set.remove(user)
        for group_name in data.cleaned_data.get('groups'):
            group = Group.objects.get(name=group_name) 
            group.user_set.add(user)
        return data.cleaned_data

    class Meta:
        model = LogisticsProfile
        exclude = ('user', 'location', 'designation')


class UploadFacilityFileForm(forms.Form):
    file = forms.FileField()


class ProductForm(forms.ModelForm):

    class Meta:
        model = Product
        exclude = ('product_code', 'description', 'equivalents', 'is_active')


class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput())
    repeat_password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        exclude = ('is_active', 'is_staff', 'is_superuser', 'last_login', 'date_joined',
                   'groups', 'user_permissions')

    def clean(self):
        ret = super(UserForm, self).clean()
        if self.cleaned_data['password'] != self.cleaned_data['repeat_password']:
            raise forms.ValidationError('Provided passwords do not match!')
        return ret

    def save(self, commit=True):
        user = super(UserForm, self).save(commit=commit)
        if commit:
            user.set_password(self.cleaned_data['password'])
            user.save()
        return user
