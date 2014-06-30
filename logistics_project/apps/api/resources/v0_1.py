from tastypie.authentication import BasicAuthentication
from tastypie.authorization import ReadOnlyAuthorization
from tastypie.exceptions import BadRequest
from tastypie.resources import Resource, ModelResource
from logistics.models import Product
from tastypie.utils.validate_jsonp import is_valid_jsonp_callback_value
from logistics_project.apps.api import ApiSerializer


class CustomResource(ModelResource):
    # copy from Resource class
    def serialize(self, request, data, format, options={}):
        """
        Given a request, data and a desired format, produces a serialized
        version suitable for transfer over the wire.

        Mostly a hook, this uses the ``Serializer`` from ``Resource._meta``.
        """
        options = options or {'type': self.type}

        if 'text/javascript' in format:
            # get JSONP callback name. default to "callback"
            callback = request.GET.get('callback', 'callback')

            if not is_valid_jsonp_callback_value(callback):
                raise BadRequest('JSONP callback name is invalid.')

            options['callback'] = callback

        return self._meta.serializer.serialize(data, format, options)



class CustomResourceMeta(object):
    authorization = ReadOnlyAuthorization()
    authentication = BasicAuthentication()
    default_format = 'application/json'

class ProductResources(CustomResource):
    type = "product_list"

    class Meta(CustomResourceMeta):
        max_limit = None
        serializer = ApiSerializer()
        queryset = Product.objects.all()
        include_resource_uri = False
        fields = ['name', 'units', 'sms_code', 'description', 'is_active']
        list_allowed_methods = ['get']