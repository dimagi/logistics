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
        if self.name:
            return self.name
        return unicode(self.pk)

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
        
    def has_responsibility(self, code):
        if not self.role:
            return False
        responsibilities = self.role.responsibilities.values_list('code', flat=True)
        if code in responsibilities:
            return True
        return False
    
    def commodities_reported(self):
        """ this user is responsible for reporting these commodities """
        if settings.LOGISTICS_STOCKED_BY == settings.STOCKED_BY_USER: 
            # do a join on all commodities associated with this user
            return Product.objects.filter(is_active=True).filter(reported_by=self)
        elif settings.LOGISTICS_STOCKED_BY == settings.STOCKED_BY_FACILITY: 
            # look for products with active ProductStocks linked to user's facility
            return Product.objects.filter(productstock__supply_point=self.supply_point, 
                                          productstock__is_active=True, 
                                          is_active=True)
        elif settings.LOGISTICS_STOCKED_BY == settings.STOCKED_BY_PRODUCT: 
            # all active Products in the system
            return Product.objects.filter(is_active=True)
        raise ImproperlyConfigured("LOGISTICS_STOCKED_BY setting is not configured correctly")
