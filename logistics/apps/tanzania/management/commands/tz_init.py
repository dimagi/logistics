from django.core.management.base import BaseCommand
from logistics.loader.base import load_roles, load_report_types

class Command(BaseCommand):
    help = "Initialize static data for malawi"

    def handle(self, *args, **options):
        load_report_types()
        load_roles()
        