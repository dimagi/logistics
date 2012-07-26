from django.db import models


class Organization(models.Model):
	"""
	An organization. Used for reporting purposes. For now contacts  	
	may belong to at most 1 organization.
	"""
	name = models.CharField(max_length=128)

	def __unicode__(self):
		return self.name
