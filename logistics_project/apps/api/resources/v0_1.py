from django.contrib.auth.models import User
from tastypie.authentication import BasicAuthentication
from tastypie.authorization import ReadOnlyAuthorization
from tastypie.resources import ModelResource
from rapidsms.contrib.locations.models import Point, Location
from tastypie import fields
from logistics.models import Product, LogisticsProfile, SupplyPoint
from rapidsms.models import Contact, Connection



class CustomResourceMeta(object):
    authorization = ReadOnlyAuthorization()
    authentication = BasicAuthentication()
    default_format = 'application/json'


class ProductResources(ModelResource):

    class Meta(CustomResourceMeta):
        max_limit = None
        queryset = Product.objects.all()
        include_resource_uri = False
        fields = ['name', 'units', 'sms_code', 'description', 'is_active']
        list_allowed_methods = ['get']

class UserResource(ModelResource):
    username = fields.CharField('username', null=True)

    class Meta(CustomResourceMeta):
        queryset = User.objects.all()
        list_allowed_methods = ['get']
        fields = ['username', 'first_name', 'last_name', 'email', 'password', 'is_staff', 'is_active', 'is_superuser',
                  'last_login', 'date_joined']
        include_resource_uri = False


class WebUserResources(ModelResource):
    user = fields.ToOneField(UserResource, 'user', full=True)
    location = fields.IntegerField('location_id', null=True)
    supply_point = fields.IntegerField('supply_point_id', null=True)

    def get_object_list(self, request):
        objects = super(WebUserResources, self).get_object_list(request)
        date = request.GET.get('date', None)
        if not date:
            return objects.all()
        return objects.filter(user__date_joined__gt=date)

    def dehydrate(self, bundle):
        bundle.data['user'].data['location'] = bundle.data['location']
        bundle.data['user'].data['supply_point'] = bundle.data['supply_point']
        bundle.data = bundle.data['user'].data
        return bundle

    class Meta(CustomResourceMeta):
        max_limit = None
        queryset = LogisticsProfile.objects.all()
        include_resource_uri = False
        list_allowed_methods = ['get']
        fields = ['location', 'supply_point']

class PointResource(ModelResource):
    latitude = fields.CharField('latitude')
    longitude = fields.CharField('longitude')

    class Meta(CustomResourceMeta):
        queryset = Point.objects.all()
        list_allowed_methods = ['get']
        fields = ['latitude', 'longitude']
        include_resource_uri = False

class LocationResources(ModelResource):
    id = fields.IntegerField('id')
    name = fields.CharField('name')
    type = fields.CharField('type')
    parent_id = fields.IntegerField('parent_id', null=True)
    points = fields.ToOneField(PointResource, 'point', full=True, null=True)
    code = fields.CharField('code')
    groups = fields.ListField(null=True, default=[])

    class Meta(CustomResourceMeta):
        queryset = Location.objects.all()
        list_allowed_methods = ['get']
        details_allowed_methods = ['get']
        fields = ['id', 'name', 'parent_id', 'code', 'groups']
        include_resource_uri = False

    def get_object_list(self, request, **kwargs):
        objects = super(LocationResources, self).get_object_list(request)
        date = request.GET.get('date', None)
        type = request.GET.get('loc_type', None)

        kwargs = {}

        if date:
            kwargs['date_updated__gt'] = date

        if type:
            kwargs['type__slug'] = type

        if kwargs:
            return objects.filter(**kwargs)
        else:
            return objects.all()

    def dehydrate(self, bundle):
        try:
            sp = SupplyPoint.objects.get(pk=bundle.data['id'])
            bundle.data['groups'] = list(sp.groups.all())
        except SupplyPoint.DoesNotExist:
            bundle.data['groups'] = []
        bundle.data['latitude'] = ""
        bundle.data['longitude'] = ""
        if bundle.data['points']:
            bundle.data['latitude'] = bundle.data['points'].data['latitude']
            bundle.data['longitude'] = bundle.data['points'].data['longitude']
        del bundle.data['points']
        return bundle


class SMSUserResources(ModelResource):
    name = fields.CharField('name')
    email = fields.CharField('email', null=True)
    role = fields.CharField('role', null=True)
    supply_point = fields.IntegerField('supply_point_id', null=True)
    is_active = fields.CharField('is_active')

    def get_object_list(self, request):
        objects = super(SMSUserResources, self).get_object_list(request)
        date = request.GET.get('date', None)
        if not date:
            return objects.all()
        return objects.filter(date_updated__gt=date)

    def dehydrate(self, bundle):
        try:
            connection = Connection.objects.get(contact_id=bundle.data['id'])
            bundle.data['backend'] = str(connection.backend)
            bundle.data['phone_numbers'] = [connection.identity]
        except Connection.DoesNotExist:
            bundle.data['backend'] = ""
            bundle.data['phone_numbers'] = []
        return bundle

    class Meta(CustomResourceMeta):
        queryset = Contact.objects.all()
        include_resource_uri = False
        list_allowed_methods = ['get']
        fields = ['id', 'name', 'email', 'role', 'supply_point', 'is_active']
