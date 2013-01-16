from django.core.management.base import BaseCommand
from logistics_project.apps.tanzania.loader import load_locations_from_path
from django.conf import settings

class Command(BaseCommand):
    help = "Initialize static data for tanzania"

    def handle(self, *args, **options):
        load_locations_from_path(settings.STATIC_LOCATIONS)
