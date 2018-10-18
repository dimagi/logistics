from django.core.management.base import BaseCommand


from logistics_project.apps.malawi.generator import generate

class Command(BaseCommand):
    help = "Generate sample data for malawi"

    def handle(self, *args, **options):
        generate()
