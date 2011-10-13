from django.core.management.base import BaseCommand
from logistics_project.apps.tanzania.loader import load_schedules
from scheduler.models import EventSchedule

class Command(BaseCommand):
    help = "Initialize the reminder schedules for tanzania"

    def handle(self, *args, **options):
        start_count = EventSchedule.objects.count()
        load_schedules()
        end_count = EventSchedule.objects.count()
        print "Loaded scheduled events. Before running %s, after: %s" % (start_count, end_count)
        