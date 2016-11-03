from django.db import models
from logistics.models import Product
from logistics.util import config


class MalawiSupplyPointExtension(models.Model):

    class Meta:
        abstract = True

    def commodities_stocked(self):
        if self.type_id == config.SupplyPointCodes.HSA:
            return super(MalawiSupplyPointExtension, self).commodities_stocked().filter(type__base_level=config.BaseLevel.HSA)
        elif self.type_id == config.SupplyPointCodes.FACILITY:
            return Product.objects.filter(is_active=True, type__base_level=config.BaseLevel.FACILITY)

        return super(MalawiSupplyPointExtension, self).commodities_stocked()

    def commodities_not_stocked(self):
        if self.type_id == config.SupplyPointCodes.HSA:
            return list(
                set(Product.objects.filter(is_active=True, type__base_level=config.BaseLevel.HSA)) -
                set(self.commodities_stocked())
            )
        elif self.type_id == config.SupplyPointCodes.FACILITY:
            # Even though this always returns empty list right now, we'll still calculate it the right
            # way in case some day commodities_stocked() is implemented a different way.
            return list(
                set(Product.objects.filter(is_active=True, type__base_level=config.BaseLevel.FACILITY)) -
                set(self.commodities_stocked())
            )

        return super(MalawiSupplyPointExtension, self).commodities_not_stocked()
