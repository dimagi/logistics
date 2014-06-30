from tastypie.serializers import Serializer
import json


class ApiSerializer(Serializer):

    def serialize(self, bundle, format='application/json', options={}):
        data = super(ApiSerializer, self).serialize(bundle, format, options)
        dict_data = json.loads(data)
        return json.dumps({options['type']: dict_data['objects']})

