from django.contrib.auth.models import User
from django.http import HttpResponse
from pip.commands import bundle
from tastypie.authentication import BasicAuthentication
from tastypie.authorization import ReadOnlyAuthorization
from tastypie.resources import ModelResource
from tastypie import fields
from logistics.models import Product, LogisticsProfile
from logistics_project.apps.api.models import ApiCheckpoint
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


class ConnectionResource(ModelResource):
    backend = fields.CharField('backend', null=True)
    identity = fields.CharField('identity', null=True)

    class Meta(CustomResourceMeta):
        queryset = Connection.objects.all()
        list_allowed_methods = ['get']
        fields = ['backend', 'identity']
        include_resource_uri = False


class SMSUserResource(ModelResource):
    connection = fields.ToOneField(ConnectionResource, 'connection', null=True, full=True)
    name = fields.CharField('name')
    email = fields.CharField('email', null=True)
    role = fields.CharField('role', null=True)
    supply_point = fields.CharField('supply_point', null=True)
    is_active = fields.CharField('is_active')


    def get_list(self, request, **kwargs):
        response = super(SMSUserResource, self).get_list(request)
        return response


    def dehydrate(self, bundle):
        bundle.data['backend'] = None
        bundle.data['phone_numbers'] = []
        if bundle.data['connection']:
            bundle.data['backend'] = bundle.data['connection'].data['backend']
            bundle.data['phone_numbers'] = [bundle.data['connection'].data['identity']]
        del bundle.data['connection']
        return bundle

    class Meta(CustomResourceMeta):
        max_limit = None
        queryset = Contact.objects.all()
        include_resource_uri = False
        list_allowed_methods = ['get']
        fields = ['name', 'email', 'role', 'supply_point', 'is_active']


class CheckpointResource(ModelResource):
    class Meta(CustomResourceMeta):
        max_limit = None
        queryset = ApiCheckpoint.objects.all()
        include_resource_uri = False
        list_allowed_methods = ['post']

    def post_list(self, request, **kwargs):

        return HttpResponse('ok')
        # """
        # Exactly copied from https://github.com/toastdriven/django-tastypie/blob/v0.9.14/tastypie/resources.py#L1314
        # (BSD licensed) and modified to catch Exception and not returning traceback
        # """
        # deserialized = self.deserialize(request, request.raw_post_data, format=request.META.get('CONTENT_TYPE', 'application/json'))
        # deserialized = self.alter_deserialized_detail_data(request, deserialized)
        # bundle = self.build_bundle(data=dict_strip_unicode_keys(deserialized), request=request)
        # try:
        #     updated_bundle = self.obj_create(bundle, **self.remove_api_resource_names(kwargs))
        #     location = self.get_resource_uri(updated_bundle)
        #
        #     if not self._meta.always_return_data:
        #         return http.HttpCreated(location=location)
        #     else:
        #         updated_bundle = self.full_dehydrate(updated_bundle)
        #         updated_bundle = self.alter_detail_data_to_serialize(request, updated_bundle)
        #         return self.create_response(request, updated_bundle, response_class=http.HttpCreated, location=location)
        # except AssertionError as ex:
        #     bundle.data['error_message'] = ex.message
        #     return self.create_response(request, bundle, response_class=http.HttpBadRequest)