from django.db import models

class MalawiProfileExtension(models.Model):
    
    organization = models.ForeignKey('malawi.Organization', null=True, blank=True)
    
    class Meta:
        abstract = True
    