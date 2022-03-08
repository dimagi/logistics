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
        fields = ['name', 'managed_supply_points']
        

class LogisticsProfileForm(forms.ModelForm):
    DASHBOARD_HSA = 'hsa'
    DASHBOARD_FACILITY = 'facility'
    DASHBOARD_BOTH = 'both'

    supply_point = forms.ModelChoiceField(
        queryset=SupplyPoint.objects.filter(active=True,
            type__code=config.SupplyPointCodes.DISTRICT),
        required=False,
        label='District'
    )

    def __init__(self, *args, **kwargs):
        super(LogisticsProfileForm, self).__init__(*args, **kwargs)
        self.fields['groups'] = self.get_group_field()
        self.fields['dashboard_access'] = self.get_dashboard_access_field()

    def get_group_field(self):
        groups = forms.ModelMultipleChoiceField(
            queryset=Group.objects.all(),
            required=False,
            initial=[g.id for g in self.instance.user.groups.all()],
            label='Groups'
        )
        return groups

    def get_dashboard_access_field(self):
        if self.instance.can_view_hsa_level_data and self.instance.can_view_facility_level_data:
            current_value = self.DASHBOARD_BOTH
        elif self.instance.can_view_facility_level_data:
            current_value = self.DASHBOARD_FACILITY
        else:
            current_value = self.DASHBOARD_HSA

        return forms.ChoiceField(
            required=True,
            choices=(
                (self.DASHBOARD_HSA, "HSA Only"),
                (self.DASHBOARD_FACILITY, "Facility Only"),
                (self.DASHBOARD_BOTH, "Both"),
            ),
            initial=current_value,
            label='Dashboard Access'
        )

    def set_dashboard_access_properties(self, obj):
        dashboard_access = self.cleaned_data.get('dashboard_access')
        if dashboard_access == self.DASHBOARD_BOTH:
            obj.can_view_hsa_level_data = True
            obj.can_view_facility_level_data = True
        elif dashboard_access == self.DASHBOARD_FACILITY:
            obj.can_view_hsa_level_data = False
            obj.can_view_facility_level_data = True
        else:
            obj.can_view_hsa_level_data = True
            obj.can_view_facility_level_data = False

        if obj.current_dashboard_base_level == config.BaseLevel.HSA and not obj.can_view_hsa_level_data:
            obj.current_dashboard_base_level = config.BaseLevel.FACILITY
        elif obj.current_dashboard_base_level == config.BaseLevel.FACILITY and not obj.can_view_facility_level_data:
            obj.current_dashboard_base_level = config.BaseLevel.HSA

    def clean(data):
        user = data.instance.user
        for group in Group.objects.all():
            group.user_set.remove(user)
        for group_name in data.cleaned_data.get('groups'):
            group = Group.objects.get(name=group_name) 
            group.user_set.add(user)
        return data.cleaned_data

    def save(self, commit=True):
        obj = super(LogisticsProfileForm, self).save(commit=False)

        self.set_dashboard_access_properties(obj)
        if commit:
            obj.save()

        return obj

    class Meta:
        model = LogisticsProfile
        exclude = ('user', 'location', 'designation', 'can_view_hsa_level_data',
            'can_view_facility_level_data', 'current_dashboard_base_level')


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
