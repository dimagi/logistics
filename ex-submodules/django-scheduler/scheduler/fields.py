"""
A field which can store a json object in the database. 
"""

from django.db import models
import json


class JSONField(models.TextField):
    """
    JSONField is a generic textfield that neatly serializes/unserializes
    JSON objects seamlessly
    """

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

    def from_db_value(self, value, expression, connection, context):
        return self.to_python(value)

    def get_prep_value(self, value):
        """Convert our JSON object to a string before we save"""
        return json.dumps(value)

