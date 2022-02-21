"""
A field which can store a json object in the database. 
"""

from django.db import models
from django.utils import simplejson as json

class JSONField(models.TextField):
    """
    JSONField is a generic textfield that neatly serializes/unserializes
    JSON objects seamlessly
    """

    __metaclass__ = models.SubfieldBase

    def to_python(self, value):
        """Convert our string value to JSON after we load it from the DB"""
        if value is not None and isinstance(value, basestring):
            try:
                return json.loads(value)
            except ValueError:
                # it's unclear why this is getting called in the model 
                # constructor but it is, and this catches the errors.
                pass 
        
        return value

    def get_prep_value(self, value):
        """Convert our JSON object to a string before we save"""
        value = json.dumps(value)
        return super(JSONField, self).get_prep_value(value)

