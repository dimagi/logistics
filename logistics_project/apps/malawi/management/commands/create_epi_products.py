from __future__ import unicode_literals
from django.core.management.base import BaseCommand
from logistics.models import Product, ProductType
from static.malawi.config import BaseLevel


def create_or_update_epi_products():
    epi_type, _ = ProductType.objects.get_or_create(
        code='epi',
        base_level=BaseLevel.FACILITY,
        defaults={'name': 'EPI'},
    )
    for (name, code, unit, amc, eo) in (
        ('BCG', 'BC', '1 dose', 250, 32),
        ('bOPV', 'OP', '1 dose', 450, 57),
        ('IPV', 'IP', '1 dose', 100, 13),
        ('Penta', 'PE', '1 dose', 350, 44),
        ('PCV13', 'PN', '1 dose', 350, 44),
        ('Rota', 'RO', '1 dose', 250, 32),
        ('Measles', 'ME', '1 dose', 300, 38),
        ('TTV', 'TV', '1 dose', 400, 50),
        ('Syringe 0.05mls', 'SA', '1 syringe', 1000, 100),
        ('Syringe 0.5mls', 'SB', '1 syringe', 1000, 100),
        ('Syringe 2mls', 'SC', '1 syringe', 1000, 100),
        ('Syringe 5mls', 'SD', '1 syringe', 1000, 100),
        ('Safety box', 'SF', '1 box', 2, 1),
    ):
        code = code.lower()
        product, _ = Product.objects.get_or_create(
            sms_code=code,
            defaults={'type': epi_type},
        )
        product.name = name
        product.description = name
        product.units = unit
        product.is_active = True
        product.average_monthly_consumption = amc
        product.emergency_order_level = eo
        product.type = epi_type
        product.save()


class Command(BaseCommand):
    help = "Load EPI Products"

    def handle(self, *args, **options):
        create_or_update_epi_products()
