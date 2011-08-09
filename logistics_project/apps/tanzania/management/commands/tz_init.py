from django.core.management.base import BaseCommand
from logistics_project.apps.tanzania.loader import init_static_data

class Command(BaseCommand):
    help = "Initialize static data for tanzania"

    def handle(self, *args, **options):
        init_static_data()