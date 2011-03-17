from __future__ import absolute_import
from django.db import models

class Contact(models.Model):
    # if one person wants to submit stocks for multiple facilities, then
    # they'll have to create multiple contacts for themselves
    role = models.ForeignKey("logistics.ContactRole", null=True, blank=True)
    facility = models.ForeignKey("logistics.Facility",null=True,blank=True)
    needs_reminders = models.BooleanField(default=True)
    commodities = models.ManyToManyField("logistics.Product", 
                                         help_text="User manages these commodities.",
                                         related_name="reported_by",
                                         blank=True, null=True)

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

    def supervisor(self):
        """
        If this contact is not a supervisor, message all staff with a supervisor responsibility at this facility
        If this contact is a supervisor, message the super at the next facility up
        Question: this looks like business/controller logic. Should it really be in 'model' code?
        """

        if SUPERVISOR not in self.role.responsibilities.objects.all():
            return Contact.objects.filter(facility=self.facility,
                                                   role=SUPERVISOR)
        return Contact.objects.filter(facility=self.facility.parentsdp(),
                                               role=SUPERVISOR)
        