from django.contrib.auth.models import User, Group
from django.db.models.aggregates import Count
from tastypie.authentication import BasicAuthentication
from tastypie.authorization import ReadOnlyAuthorization
from tastypie.constants import ALL_WITH_RELATIONS
from tastypie.resources import ModelResource
from tastypie import fields
from logistics.models import Product, ProductType, LogisticsProfile, SupplyPoint, StockTransaction, ProductStock
from rapidsms.models import Contact, Connection
from rapidsms.contrib.locations.models import Point, Location
from email_reports.models import WeeklyReportSubscription, MonthlyReportSubscription, ReportSubscription, \
    DailyReportSubscription


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
        queryset = User.objects.filter(is_active=True)
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
                                                   product__is_active=True).values_list(*['product'], flat=True)),
        full=True, null=True)
    incharges = fields.ListField(null=True, default=[])

    def dehydrate(self, bundle):
        products_obj = bundle.data['products']
        products = []
        if products_obj:
            for ps in products_obj:
                products.append(ps.obj.sms_code)
        bundle.data['products'] = products
        bundle.data['incharges'] = [incharge.pk for incharge in bundle.obj.incharges()]
        return bundle

    class Meta(CustomResourceMeta):
        queryset = SupplyPoint.objects.all()
        list_allowed_methods = ['get']
        include_resource_uri = False
        fields = [
            'id', 'name', 'active', 'type', 'code', 'last_reported',
            'groups', 'location_id', 'products', 'incharges'
        ]
        filtering = {
            'id': ('exact', ),
            'active': ('exact', ),
            'last_reported': ('isnull', )
        }


class NewSMSUserResources(ModelResource):
    name = fields.CharField('name')
    email = fields.CharField('email', null=True)
    role = fields.CharField('role', null=True)
    supply_point = fields.ToOneField(SupplyPointResources, 'supply_point', full=True, null=True)
    is_active = fields.CharField('is_active')
    family_name = fields.CharField('family_name')
    needs_reminders = fields.BooleanField('needs_reminders')

    def get_object_list(self, request):
        objects = super(NewSMSUserResources, self).get_object_list(request)
        if bool(request.GET.get('with_more_than_one_number', False)):
            return objects.annotate(connections_count=Count('connection')).filter(connections_count__gt=1)
        return objects

    def dehydrate(self, bundle):
        default_connection = bundle.obj.default_connection
        connections = [
            {'backend': connection.backend, 'phone_number': connection.identity,
             'default': default_connection == connection}
            for connection in Connection.objects.filter(contact=bundle.obj)
        ]
        bundle.data['phone_numbers'] = connections
        return bundle

    class Meta(CustomResourceMeta):
        queryset = Contact.objects.filter(is_active=True).order_by('id')
        include_resource_uri = False
        list_allowed_methods = ['get']
        fields = ['id', 'language', 'name', 'email', 'role',
                  'supply_point', 'is_active', 'date_updated', 'family_name', 'needs_reminders']
        filtering = {
            'date_updated': ('gte', ),
            'needs_reminders': ('exact', )
        }
        ordering = ['date_updated']


class SMSUserResources(ModelResource):
    name = fields.CharField('name')
    email = fields.CharField('email', null=True)
    role = fields.CharField('role', null=True)
    supply_point = fields.ToOneField(SupplyPointResources, 'supply_point', full=True, null=True)
    is_active = fields.CharField('is_active')
    family_name = fields.CharField('family_name')

    def dehydrate(self, bundle):
        connection = bundle.obj.default_connection
        if connection:
            bundle.data['backend'] = str(connection.backend)
            bundle.data['phone_numbers'] = [connection.identity]
            bundle.data['to'] = connection.to if connection.to is not None else ""
        else:
            bundle.data['backend'] = ""
            bundle.data['phone_numbers'] = []
            bundle.data['to'] = ""
        return bundle

    class Meta(CustomResourceMeta):
        queryset = Contact.objects.filter(is_active=True).order_by('id')
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
    contact = fields.ToOneField(NewSMSUserResources, 'contact', null=True, full=True)

    def dehydrate(self, bundle):
        bundle.data['user'].data['location'] = bundle.data['location']
        bundle.data['user'].data['supply_point'] = bundle.data['supply_point']
        bundle.data['user'].data['sms_notifications'] = bundle.data['sms_notifications']
        bundle.data['user'].data['organization'] = bundle.data['organization']
        bundle.data['user'].data['contact'] = bundle.data['contact']
        program = bundle.obj.program
        bundle.data['user'].data['program'] = program.code if program else None
        bundle.data = bundle.data['user'].data
        return bundle

    class Meta(CustomResourceMeta):
        max_limit = None
        queryset = LogisticsProfile.objects.filter(user__is_active=True).order_by('user__date_joined', 'id')
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
        queryset = Location.objects.all().order_by('id')
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


class StockTransactionResources(ModelResource):
    supply_point = fields.IntegerField('supply_point_id', null=True)

    def dehydrate(self, bundle):
        bundle.data['product'] = bundle.obj.product.sms_code
        bundle.data['report_type'] = bundle.obj.product_report.report_type
        return bundle

    def apply_filters(self, request, applicable_filters):
        if 'supply_point_id__exact' in applicable_filters:
            value = applicable_filters['supply_point_id__exact']
            del applicable_filters['supply_point_id__exact']
            applicable_filters['supply_point__id'] = value
        return super(StockTransactionResources, self).apply_filters(request, applicable_filters)

    class Meta(CustomResourceMeta):
        queryset = StockTransaction.objects.all().order_by('date', 'id')
        include_resource_uri = False
        list_allowed_methods = ['get']
        excludes = ['id', ]
        filtering = {
            "date": ('gte', 'lte'),
            "supply_point": ('exact', )
        }
        ordering = ['date']


class ToManyFieldForUsers(fields.ToManyField):
    def dehydrate(self, bundle, for_list=True):
        related_objects = super(ToManyFieldForUsers, self).dehydrate(bundle, for_list)
        only_emails = []
        if related_objects:
            for ro in related_objects:
                only_emails.append(ro.obj.email)
        return only_emails


class DailyScheduledReportResources(ModelResource):
    hours = fields.IntegerField('hours')
    report = fields.CharField('report__display_name')
    users = ToManyFieldForUsers(UserResource, 'users', null=True, full=True)
    view_args = fields.CharField('_view_args')

    class Meta(CustomResourceMeta):
        queryset = DailyReportSubscription.objects.all()
        include_resource_uri = False
        fields = ['hours', 'report', 'users', 'view_args']
        list_allowed_methods = ['get']


class WeeklyScheduledReportResources(ModelResource):
    hours = fields.IntegerField('hours')
    day_of_week = fields.IntegerField('day_of_week')
    report = fields.CharField('report__display_name')
    users = ToManyFieldForUsers(UserResource, 'users', null=True, full=True)
    view_args = fields.CharField('_view_args')

    class Meta(CustomResourceMeta):
        queryset = WeeklyReportSubscription.objects.all()
        include_resource_uri = False
        fields = ['hours', 'day_of_week', 'report', 'users', 'view_args']
        list_allowed_methods = ['get']


class MonthlyScheduledReportResources(ModelResource):
    hours = fields.IntegerField('hours')
    day_of_month = fields.IntegerField('day_of_month')
    report = fields.CharField('report__display_name')
    view_args = fields.CharField('_view_args')
    users = ToManyFieldForUsers(UserResource, 'users', null=True, full=True)

    class Meta(CustomResourceMeta):
        queryset = MonthlyReportSubscription.objects.all()
        include_resource_uri = False
        fields = ['hours', 'day_of_month', 'report', 'users', 'view_args']
        list_allowed_methods = ['get']
