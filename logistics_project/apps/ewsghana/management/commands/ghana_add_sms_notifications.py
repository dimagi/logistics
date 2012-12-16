from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = "Add web reminders and sms notifications"

    def handle(self, *args, **options):
        self.add_new_alerts()

    def add_new_alerts(self):
        from rapidsms.contrib.scheduler.models import EventSchedule, set_weekly_event

        # set up rapidsms-alerts to trigger notifications
        try:
            EventSchedule.objects.get(callback="alerts.utils.trigger_notifications")
        except EventSchedule.DoesNotExist:
            # Tuesday at 9:20 am
            set_weekly_event("alerts.utils.trigger_notifications", day=1, 
                             hour=9, minute=20)
            
        # set up rapdidsms-alerts to send out web reminders
        try:
            EventSchedule.objects.get(callback="logistics_project.apps.ewsghana.schedule.reminder_to_visit_website")
        except EventSchedule.DoesNotExist:
            # every quarter, on the 4th of the month, at 10:03 am
            schedule = EventSchedule(callback="logistics_project.apps.ewsghana.schedule.reminder_to_visit_website", 
                                     months=set([1,4,7,10]), days_of_month=set([4]), 
                                     hours=set([10]), minutes=set([3]))
            schedule.save()
