from django.db import models
from django.db.models.fields import CharField


class Organization(models.Model):
    """
    An organization. Used for reporting purposes. For now contacts
    may belong to at most 1 organization.
    """
    # TODO: should this model belong to the actual logistics rapidsms app?
    
    name = CharField(max_length=128)
    
    def __unicode__(self):
        return self.name