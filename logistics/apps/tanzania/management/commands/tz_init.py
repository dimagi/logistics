from django.core.management.base import BaseCommand
from logistics.loader.base import load_roles, load_report_types
from logistics.apps.tanzania.loader import init_static_data

class Command(BaseCommand):
    help = "Initialize static data for malawi"

    def handle(self, *args, **options):
        init_static_data()