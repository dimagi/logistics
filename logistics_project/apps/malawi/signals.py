from django.db import transaction
from django.db.models.signals import post_save
from rapidsms.models import Contact
from static.malawi.config import SupplyPointCodes


@transaction.atomic
def deactivate_hsa_location(sender, instance, created, **kwargs):
    if instance.is_hsa and not instance.is_active:
        # also make sure to deactivate the location and supply
        # point if necessary
        if instance.supply_point:
            sp = instance.supply_point
            if sp.type.code != SupplyPointCodes.HSA:
                print('Refusing to deactivate location because HSA was registered to a non-HSA supply point %s (%s).' % (sp, sp.type))
                return

            # Don't deactivate the supply point if other active contacts belong to it
            if sp.active_contact_set.count() > 0:
                return

            if sp.active:
                sp.active = False
                sp.save()
            if sp.location and sp.location.is_active:
                sp.location.is_active = False
                sp.location.save()

post_save.connect(deactivate_hsa_location, sender=Contact)
