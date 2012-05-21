from django.contrib.auth.models import User

from logistics.models import SupplyPoint, Product, SupplyPointGroup, SupplyPoint_Groups, StockTransaction

from logistics_project.apps.tanzania.models import SupplyPointStatus
from logistics_project.apps.tanzania.core.models import UserProfile, Organization, OrganizationProduct, 
                                                        OrganizationProductAmountChangeHistory, 
                                                        DeliveryResponse, SOHSubmission, RRSubmission,
                                                        SupervisionSubmission,


def populate_metadata():
    # populate user roles
    for u in User.objects.all():
        up = UserProfile(user = u, user_role="user")
        up.save()

    # map supply points to delivery groups
    spgmap = {}
    for spg in SupplyPoint_Groups.objects.all():
        spgmap[spg.supply_point.id] = spg.supplypointgroup

    # populate organizations and orgproducts
    for sp in SupplyPoint.objects.all():
        o = Organization(supply_point = sp, parent_organization = sp.supplied_by, delivery_group = spgmap[sp.id], type = sp.type)
        o.save()
        for p in Product.objects.all():
            op = OrganizationProduct(organization = o, product = p)
            op.save()

def populate_historical_data():
    # populate stock data
    for op in OrganizationProduct.objects.all():
        trans = StockTransaction.objects.filter(supply_point = op.organization.supply_point, product = op.product).order_by('date')
        for st in trans:
            opa = OrganizationProductAmountChangeHistory(organization_product=op, date = st.date, change_amount = st.quantity, current_total = st.ending_balance, stocked_out=st.ending_balance<=0)

    # populate submission data
    # TODO: FIX, this isn't right...
    # 
    # on time, late, not submitted + received, not received + no response, reminder sent
    # vs
    # not received, not submitted, received, reminder sent, submitted
    # 
    # la_fac, del_del
    # 
    for sps in SupplyPointStatus.objects.all():
        org = Organization.objects.get(supply_point = sps.supply_point)
        if sps.status_type=='del_fac':
            DeliveryResponse(organization = org, date = sps.status_date, response = status_value)
        if sps.status_type=='del_dist':
            DeliveryResponse(organization = org, date = sps.status_date, response = status_value)
        elif sps.status_type=='soh_fac':
            SOHSubmission(organization = org, date = sps.status_date, response = status_value)
        elif sps.status_type=='rr_fac':
            RRSubmission(organization = org, date = sps.status_date, response = status_value)
        if sps.status_type=='rr_dist':
            DeliveryResponse(organization = org, date = sps.status_date, response = status_value)
        elif sps.status_type=='super_fac':
            SupervisionSubmission(organization = org, date = sps.status_date, response = status_value)

def populate_unrec_sms():
    pass
