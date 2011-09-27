from django.core.management.base import BaseCommand, CommandError
from alerts.utils import auto_escalate, reconcile_users

class Command(BaseCommand):
    def handle(self, *args, **options):
        auto_escalate()
        reconcile_users()
