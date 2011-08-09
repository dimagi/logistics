__author__ = 'ternus'
import oldmodels as old_models
import logistics.apps.logistics.models as new_models
from rapidsms.models import Contact, ConnectionBase

def migrate():


    for product in old_models.Product.objects.all():
        p = new_models.Product(
            name=product.name,
            units=product.units,
            sms_code=product.sms_code,
            description=product.description
        )
        p.save()

    for p in old_models.ProductReportType.objects.all():
        r = new_models.ProductReportType(name=p.name,sms_code=p.sms_code)
        r.save()

    # Necessary because there's no slug field 
    types = (
        ("MOHSW", "moh"),
        ("REGION", "reg"),
        ("DISTRICT", "dis"),
        ("FACILITY", "fac")
    )

    for t in types:
        nt = new_models.SupplyPointType(
            name = t[0],
            code = t[1]
        )
        nt.save()

    for object in old_models.ServiceDeliveryPoint.objects.all():
        if new_models.SupplyPoint.objects.filter(name=object.name).exists():
            return

        l = new_models.Location(point=object.point if object.point else None,
                                type=object.type,
                                parent_type=object.parent_type,
                                parent_id=object.parent_id,
                                parent=object.parent)
        l.save()
        sp = new_models.SupplyPoint(
                    name = object.sdp_name,
                    is_active = object.active,
                    location = l,
                    type = new_models.SupplyPointType.objects.get(name=object.type.name))
        if new_models.SupplyPoint.objects.filter(name = sp.location.parent.name).exists():
            sp.supplied_by = new_models.SupplyPoint.objects.get(name = sp.location.parent.name)

        sp.save()
        
        for a in old_models.ActiveProduct.objects.filter(service_delivery_point=object):
            ps = new_models.ProductStock(is_active = a.is_active,
                                         supply_point = sp,
                                         quantity = a.current_quantity,
                                         product = new_models.Product.objects.get(sms_code=a.product.sms_code))
            ps.save()

    roles = (
        ("Facility in-charge", "ic"),
        ("DMO", "dm"),
        ("RMO", "rm"),
        ("District Pharmacist", "dp"),
        ("MOHSW", "mh"),
        ("MSD", "ms")
    )

    for r in roles:
        c = new_models.ContactRole(name=r[0], code=r[1])
        c.save()
    for oc in old_models.ContactDetail.objects.all():
        c = Contact(
            name = oc.name,
            role = new_models.ContactRole.objects.get(name=oc.role.name),
            supply_point=new_models.SupplyPoint.objects.get(name=oc.service_delivery_point.name)
        )
        c.save()
        for cb in ConnectionBase.objects.filter(contact=oc):
            cb.contact = c
            cb.save()
