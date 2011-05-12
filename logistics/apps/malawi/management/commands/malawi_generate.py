from django.core.management.base import BaseCommand
from dimagi.utils.couch.database import get_db

from logistics.apps.malawi.generator import generate

class Command(BaseCommand):
    help = "Generate sample data for malawi"

    def handle(self, *args, **options):
        generate()