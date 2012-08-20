from __future__ import absolute_import
from django.db import models
from rapidsms.models import Contact

class LogisticsProfile(models.Model):
    organization = models.CharField(max_length=255, blank=True, null=True)
    contact = models.OneToOneField(Contact, null=True, blank=True)

    class Meta:
        abstract = True
    
    def get_or_create_contact(self):
        if self.contact is not None:
            return self.contact
        contact = Contact(name=self.user.username)
        contact.save()
        self.contact = contact
        self.save()
        return self.contact

