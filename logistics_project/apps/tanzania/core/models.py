from django.db import models
from django.contrib.auth.models import User

from logistics.models import SupplyPoint, SupplyPointGroup, SupplyPointType, Product, ContactRole


class UserRole(object):
	"""
	type of user, for reports, visibility, etc
	  # NOTE: Should probably make this compatible with ContactRole
	  # NOTE: Should consider using something like: https://github.com/dabapps/django-user-roles
	"""
	ADMIN = "admin"
	SUPERVISOR = "supervisor"
	USER = "user"
	CHOICES = [ADMIN, SUPERVISOR, USER]
	ROLE_CHOICES = ((val, val) for val in CHOICES)

class UserProfile(models.Model):
	"""
	auth-User profile to manage information about the user and potential differences in visibility
	"""
	user = models.ForeignKey(User)
	user_role = models.CharField(max_length=20, choices=UserRole.ROLE_CHOICES)
	create_date = models.DateTimeField(auto_now_add=True)
	update_date = models.DateTimeField(auto_now=True)

class Organization(models.Model):
	"""
	SupplyPoint plus information specific to Tanzania implementation
	"""
	supply_point = models.ForeignKey(SupplyPoint)
	parent_organization = models.ForeignKey('self', blank=True, null=True)
	delivery_group = models.ForeignKey(SupplyPointGroup)
	type = models.ForeignKey(SupplyPointType)
	create_date = models.DateTimeField(auto_now_add=True)
	update_date = models.DateTimeField(auto_now=True)

class OrganizationProduct(models.Model):
	"""
	each org carries certain products
	"""
	organization = models.ForeignKey('Organization')
	product = models.ForeignKey(Product)
	create_date = models.DateTimeField(auto_now_add=True)
	update_date = models.DateTimeField(auto_now=True)

class OrganizationProductAmountChangeHistory(models.Model):
	"""
	records transactions of products at org
	"""
	organization_product = models.ForeignKey('OrganizationProduct')
	date = models.DateTimeField()
	change_amount = models.FloatField(default=0)
	current_total = models.FloatField(default=0)
	stocked_out = models.BooleanField(default=True)
	create_date = models.DateTimeField(auto_now_add=True)
	update_date = models.DateTimeField(auto_now=True)

class Alert(models.Model):
	"""
	record of alerts
	"""
	alert = models.TextField()
	dismissed = models.BooleanField(default=False)
	create_date = models.DateTimeField(auto_now_add=True)
	update_date = models.DateTimeField(auto_now=True)

	def expire_alert(self):
		"""
		placeholder to set a time period after which alert expires (is marked dismissed)
		"""
		pass

class AlertVisibility(models.Model):
	"""
	record of who should see what alerts
	"""
	alert = models.ForeignKey('Alert')
	organization = models.ForeignKey('Organization')
	user_role = models.CharField(max_length=20, choices=UserRole.ROLE_CHOICES)
	create_date = models.DateTimeField(auto_now_add=True)
	update_date = models.DateTimeField(auto_now=True)

class UnrecognizedSMS(models.Model):
	"""
	log of msgs that failed
	"""
	organization = models.ForeignKey('Organization')
	date = models.DateTimeField()
	message = models.TextField()
	contact = models.ForeignKey(User)
	msd_code = models.CharField(max_length=20)
	resolved = models.BooleanField(default=False)
	create_date = models.DateTimeField(auto_now_add=True)
	update_date = models.DateTimeField(auto_now=True)

class SubmissionResponseStatus(object):
	ON_TIME = "on time"
	LATE = "late"
	NOT_SUBMITTED = "not submitted"
	NO_RESPONSE = "no response"
	CHOICES = [ON_TIME, LATE, NOT_SUBMITTED, NO_RESPONSE]
	RESPONSE_CHOICES = ((val, val) for val in CHOICES)

class SOHSubmission(models.Model):
	"""
	stock-on-hand submission
	"""
	organization = models.ForeignKey('Organization')
	date = models.DateTimeField()
	response = models.CharField(max_length=20, choices=SubmissionResponseStatus.RESPONSE_CHOICES)
	create_date = models.DateTimeField(auto_now_add=True)
	update_date = models.DateTimeField(auto_now=True)

class RRSubmission(models.Model):
	"""
	R&R submssion
	"""
	organization = models.ForeignKey('Organization')
	date = models.DateTimeField()
	response = models.CharField(max_length=20, choices=SubmissionResponseStatus.RESPONSE_CHOICES)
	create_date = models.DateTimeField(auto_now_add=True)
	update_date = models.DateTimeField(auto_now=True)

class SupervisionSubmission(models.Model):
	"""
	Supervision submssion
	"""
	organization = models.ForeignKey('Organization')
	date = models.DateTimeField()
	response = models.CharField(max_length=20, choices=SubmissionResponseStatus.RESPONSE_CHOICES)
	create_date = models.DateTimeField(auto_now_add=True)
	update_date = models.DateTimeField(auto_now=True)

class DeliveryResponseStatus(object):
	RECEIVED = "received"
	NOT_RECEIVED = "not received"
	NO_RESPONSE = "no response"
	CHOICES = [RECEIVED, NOT_RECEIVED, NO_RESPONSE]
	RESPONSE_CHOICES = ((val, val) for val in CHOICES)

class DeliveryResponse(models.Model):
	"""
	delivery response
	"""
	organization = models.ForeignKey('Organization')
	date = models.DateTimeField()
	response = models.CharField(max_length=20, choices=DeliveryResponseStatus.RESPONSE_CHOICES)
	create_date = models.DateTimeField(auto_now_add=True)
	update_date = models.DateTimeField(auto_now=True)

############### FOR REPORTS ###################
###### Blow these away and rerun reports ######
###############################################

class DistrictSummary(models.Model):
	total_facilities = models.PositiveIntegerField(default=0)
	group_a_complete = models.PositiveIntegerField(default=0)
	group_a_total = models.PositiveIntegerField(default=0)
	group_b_complete = models.PositiveIntegerField(default=0)
	group_b_total = models.PositiveIntegerField(default=0)	
	group_c_complete = models.PositiveIntegerField(default=0)
	group_c_total = models.PositiveIntegerField(default=0)
	average_lead_time_in_days = models.FloatField(default=0)
	create_date = models.DateTimeField(auto_now_add=True)
	update_date = models.DateTimeField(auto_now=True)

class ProductAvailabilitySummary(models.Model):
	organization = models.ForeignKey('Organization')
	product = models.ForeignKey(Product)
	stocked_out = models.PositiveIntegerField(default=0)
	not_stocked_out = models.PositiveIntegerField(default=0)
	no_data = models.PositiveIntegerField(default=0)
	create_date = models.DateTimeField(auto_now_add=True)
	update_date = models.DateTimeField(auto_now=True)

class SOHPie(models.Model):
	organization = models.ForeignKey('Organization')
	date = models.DateTimeField()
	on_time = models.PositiveIntegerField(default=0)
	late = models.PositiveIntegerField(default=0)
	not_submitted = models.PositiveIntegerField(default=0)
	not_responding = models.PositiveIntegerField(default=0)
	historical_response_rate = models.FloatField(default=0)
	create_date = models.DateTimeField(auto_now_add=True)
	update_date = models.DateTimeField(auto_now=True)

class RRPie(models.Model):
	organization = models.ForeignKey('Organization')
	date = models.DateTimeField()
	on_time = models.PositiveIntegerField(default=0)
	late = models.PositiveIntegerField(default=0)
	not_submitted = models.PositiveIntegerField(default=0)
	not_responding = models.PositiveIntegerField(default=0)
	historical_response_rate = models.FloatField(default=0)
	create_date = models.DateTimeField(auto_now_add=True)
	update_date = models.DateTimeField(auto_now=True)

class SupervisionPie(models.Model):
	organization = models.ForeignKey('Organization')
	date = models.DateTimeField()
	on_time = models.PositiveIntegerField(default=0)
	late = models.PositiveIntegerField(default=0)
	not_submitted = models.PositiveIntegerField(default=0)
	not_responding = models.PositiveIntegerField(default=0)
	historical_response_rate = models.FloatField(default=0)
	create_date = models.DateTimeField(auto_now_add=True)
	update_date = models.DateTimeField(auto_now=True)

class DeliveryPie(models.Model):
	organization = models.ForeignKey('Organization')
	date = models.DateTimeField()
	received = models.PositiveIntegerField(default=0)
	not_received = models.PositiveIntegerField(default=0)
	not_responding = models.PositiveIntegerField(default=0)
	historical_response_rate = models.FloatField(default=0)
	average_lead_time_in_days = models.FloatField(default=0)
	create_date = models.DateTimeField(auto_now_add=True)
	update_date = models.DateTimeField(auto_now=True)




