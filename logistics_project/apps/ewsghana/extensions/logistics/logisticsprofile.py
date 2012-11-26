from __future__ import absolute_import
from django.db import models
from rapidsms.models import Contact
from logistics.models import ProductType

class LogisticsProfile(models.Model):
    organization = models.CharField(max_length=255, blank=True, null=True)
    contact = models.OneToOneField(Contact, null=True, blank=True)
    program = models.ForeignKey(ProductType, blank=True, null=True)

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

    def deactivate(self):
        if self.contact:
            self.contact.deactivate()
        self.is_active = False
        self.save()

