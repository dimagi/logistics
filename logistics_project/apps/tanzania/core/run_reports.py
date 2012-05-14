from django.contrib.auth.models import User

from logistics.models import SupplyPoint, Product, SupplyPointGroup, SupplyPoint_Groups, StockTransaction

from logistics_project.apps.tanzania.models import SupplyPointStatus
from logistics_project.apps.tanzania.core.models import UserProfile, Organization, OrganizationProduct, 
														OrganizationProductAmountChangeHistory, 
														DeliveryResponse, SOHSubmission, RRSubmission,
														SupervisionSubmission,

def clear_out_reports():
	pass
	
def populate_report_data():
	pass