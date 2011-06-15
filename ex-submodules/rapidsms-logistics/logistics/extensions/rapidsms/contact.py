from __future__ import absolute_import
from django.db import models

class Contact(models.Model):
    # if one person wants to submit stocks for multiple facilities, then
    # they'll have to create multiple contacts for themselves
    role = models.ForeignKey("logistics.ContactRole", null=True, blank=True)
    supply_point = models.ForeignKey("logistics.SupplyPoint", null=True, blank=True)
    needs_reminders = models.BooleanField(default=True)
    commodities = models.ManyToManyField("logistics.Product", 
                                         help_text="User manages these commodities.",
                                         related_name="reported_by",
                                         blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_approved = models.BooleanField(default=False)

    class Meta:
        abstract = True
        verbose_name = "Logistics Contact"

    def __unicode__(self):
        return self.name

    @property
    def phone(self):
        if self.default_connection:
            return self.default_connection.identity
        else:
            return " "

    
    @property
    def last_message(self):
        if self.message_set.count() > 0:
            return self.message_set.order_by("-date")[0]