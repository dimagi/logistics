from django.contrib.auth.models import User, Group
from tastypie.authentication import BasicAuthentication
from tastypie.authorization import ReadOnlyAuthorization
from tastypie.constants import ALL_WITH_RELATIONS
from tastypie.resources import ModelResource
from tastypie import fields
from logistics.models import Product, ProductType, LogisticsProfile, SupplyPoint, StockTransaction, ProductStock
from rapidsms.models import Contact, Connection
from rapidsms.contrib.locations.models import Point, Location

class CustomResourceMeta(object):
    authorization = ReadOnlyAuthorization()
    authentication = BasicAuthentication()
    default_format = 'application/json'


class ProgramResource(ModelResource):
    code = fields.CharField('code')
    name = fields.CharField('name')

    class Meta(CustomResourceMeta):
        max_limit = None
        queryset = ProductType.objects.all()
        include_resource_uri = False
        fields = ['code', 'name']
        list_allowed_methods = ['get']


class ProductResources(ModelResource):
    program = fields.ToOneField(ProgramResource, 'type', full=True, null=True)

    class Meta(CustomResourceMeta):
        max_limit = None
        queryset = Product.objects.all()
        include_resource_uri = False
        fields = ['name', 'units', 'sms_code', 'description', 'is_active', 'program']
        list_allowed_methods = ['get']


class GroupResources(ModelResource):
    class Meta(CustomResourceMeta):
        max_limit = None
        queryset = Group.objects.all()
        include_resource_uri = False


class UserResource(ModelResource):
    username = fields.CharField('username', null=True)
    groups = fields.ToManyField(GroupResources, 'groups',
                                full=True, null=True)

    class Meta(CustomResourceMeta):
        queryset = User.objects.all()
        list_allowed_methods = ['get']
        fields = ['username', 'first_name', 'last_name', 'email', 'password', 'is_staff', 'is_active',
                  'is_superuser', 'last_login', 'date_joined']
        include_resource_uri = False
        filtering = {
            'date_joined': ('gte', )
        }


class SupplyPointResources(ModelResource):
    supplied_by = fields.IntegerField('supplied_by_id', null=True)
    supervised_by = fields.IntegerField('supervised_by_id', null=True)
    primary_reporter = fields.IntegerField('primary_reporter_id', null=True)
    groups = fields.ListField(null=True, default=[])
    active = fields.BooleanField('active')
    type = fields.CharField('type')
    location_id = fields.IntegerField('location_id', null=True)
    products = fields.ToManyField(
        ProductResources,
        attribute=lambda
            bundle: Product.objects.filter(
                id__in=ProductStock.objects.filter(supply_point=bundle.obj,
                                                   is_active=True,
                                                   product__is_active=True).values_list(*['product'], flat=True),
                is_active=True), full=True, null=True)

    def dehydrate(self, bundle):
        products_obj = bundle.data['products']
        products = []
        if products_obj:
            for ps in products_obj:
                products.append(ps.obj.sms_code)
        bundle.data['products'] = products
        return bundle


    class Meta(CustomResourceMeta):
        queryset = SupplyPoint.objects.all()
        list_allowed_methods = ['get']
        include_resource_uri = False
        fields = ['id', 'name', 'active', 'type', 'code', 'last_reported', 'groups', 'location_id', 'products']
        filtering = {
            'id': ('exact', ),
            'active': ('exact', ),
            'last_reported': ('isnull', )
        }


class SMSUserResources(ModelResource):
    name = fields.CharField('name')
    email = fields.CharField('email', null=True)
    role = fields.CharField('role', null=True)
    supply_point = fields.ToOneField(SupplyPointResources, 'supply_point', full=True, null=True)
    is_active = fields.CharField('is_active')
    family_name = fields.CharField('family_name')

    def dehydrate(self, bundle):
        try:
            connection = Connection.objects.get(id=bundle.data['id'])
            bundle.data['backend'] = str(connection.backend)
            bundle.data['phone_numbers'] = [connection.identity]
            bundle.data['to'] = connection.to if connection.to is not None else ""
        except Connection.DoesNotExist:
            bundle.data['backend'] = ""
            bundle.data['phone_numbers'] = []
            bundle.data['to'] = ""
        return bundle

    class Meta(CustomResourceMeta):
        queryset = Contact.objects.all().order_by('date_updated', 'id')
        include_resource_uri = False
        list_allowed_methods = ['get']
        fields = ['id', 'language', 'name', 'email', 'role',
                  'supply_point', 'is_active', 'date_updated', 'family_name']
        filtering = {
            'date_updated': ('gte', )
        }
        ordering = ['date_updated']


class WebUserResources(ModelResource):
    user = fields.ToOneField(UserResource, 'user', full=True)
    location = fields.IntegerField('location_id', null=True)
    supply_point = fields.IntegerField('supply_point_id', null=True)
    contact = fields.ToOneField(SMSUserResources, 'contact', null=True, full=True)

    def dehydrate(self, bundle):
        bundle.data['user'].data['location'] = bundle.data['location']
        bundle.data['user'].data['supply_point'] = bundle.data['supply_point']
        bundle.data['user'].data['sms_notifications'] = bundle.data['sms_notifications']
        bundle.data['user'].data['organization'] = bundle.data['organization']
        bundle.data['user'].data['contact'] = bundle.data['contact']
        bundle.data = bundle.data['user'].data
        return bundle

    class Meta(CustomResourceMeta):
        max_limit = None
        queryset = LogisticsProfile.objects.all().order_by('user__date_joined', 'id')
        include_resource_uri = False
        list_allowed_methods = ['get']
        fields = ['contact', 'location', 'supply_point', 'sms_notifications', 'organization']
        filtering = {
            'user': ALL_WITH_RELATIONS
        }


class PointResource(ModelResource):
    latitude = fields.CharField('latitude')
    longitude = fields.CharField('longitude')

    class Meta(CustomResourceMeta):
        queryset = Point.objects.all()
        list_allowed_methods = ['get']
        fields = ['latitude', 'longitude']
        include_resource_uri = False


class LocationResources(ModelResource):
    supply_points = fields.ToManyField(
        SupplyPointResources,
        attribute=lambda bundle: SupplyPoint.objects.filter(location=bundle.obj, active=True), full=True, null=True
    )
    points = fields.ToOneField(PointResource, 'point', full=True, null=True)
    type = fields.CharField('type')

    class Meta(CustomResourceMeta):
        queryset = Location.objects.all().order_by('date_updated', 'id')
        include_resource_uri = False
        filtering = {
            'type': ('exact', ),
            'date_updated': ('gte', ),
            'is_active': ('exact', )
        }
        ordering = ['date_updated']

    def dehydrate(self, bundle):
        bundle.data['longitude'] = ""
        bundle.data['latitude'] = ""
        if bundle.data['points']:
            bundle.data['latitude'] = bundle.data['points'].data['latitude']
            bundle.data['longitude'] = bundle.data['points'].data['longitude']
        del bundle.data['points']
        return bundle


class ProductStockResources(ModelResource):
    supply_point = fields.ToOneField(SupplyPointResources, 'supply_point', full=True, null=True)

    def dehydrate(self, bundle):
        bundle.data['use_auto_consumption'] = bundle.obj.use_auto_consumption
        bundle.data['manual_monthly_consumption'] = bundle.obj.manual_monthly_consumption
        bundle.data['product'] = bundle.obj.product.sms_code
        bundle.data['supply_point'] = bundle.obj.supply_point.id
        return bundle

    class Meta(CustomResourceMeta):
        queryset = ProductStock.objects.filter(is_active=True).order_by('last_modified', 'id')
        include_resource_uri = False
        list_allowed_methods = ['get']
        filtering = {
            "last_modified": ('gte', ),
            "supply_point": ALL_WITH_RELATIONS
        }
        ordering = ['last_modified']


class StockTransactionResources(ModelResource):
    supply_point = fields.ToOneField(SupplyPointResources, 'supply_point', full=True, null=True)

    def dehydrate(self, bundle):
        if bundle.obj.product_report:
            bundle.data['report_type'] = bundle.obj.product_report.report_type
        else:
            bundle.data['report_type'] = None

        bundle.data['product'] = bundle.obj.product.sms_code
        bundle.data['supply_point'] = bundle.obj.supply_point.id
        return bundle

    class Meta(CustomResourceMeta):
        queryset = StockTransaction.objects.all().order_by('date', 'id')
        include_resource_uri = False
        list_allowed_methods = ['get']
        excludes = ['id', ]
        filtering = {
            "date": ('gte', ),
            "supply_point": ('exact', )
        }
        ordering = ['date']
