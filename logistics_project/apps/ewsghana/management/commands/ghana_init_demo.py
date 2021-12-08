from django.core.management.base import BaseCommand
from logistics_project.apps.ewsghana import loader

class Command(BaseCommand):
    help = "Initialize static data for ghana"

    def handle(self, *args, **options):
        loader.init_static_data(demo=True)
