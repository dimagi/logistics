from django.core.management.base import BaseCommand, CommandError
from alerts.utils import trigger_notifications

class Command(BaseCommand):
    def handle(self, *args, **options):
        trigger_notifications()
