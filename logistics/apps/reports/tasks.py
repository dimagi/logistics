""" This is where we actually schedule when and how often reports get run """

from datetime import datetime
from celery.schedules import crontab
from celery.decorators import periodic_task
from logistics.apps.reports.models import DailyReportSubscription, WeeklyReportSubscription

@periodic_task(run_every=crontab(hour="*", minute="2", day_of_week="*"))
def daily_reports():    
    # this should get called every hour by celery
    reps = DailyReportSubscription.objects.filter(hours=datetime.utcnow().hour)
    _run_reports(reps)

@periodic_task(run_every=crontab(hour="*", minute="3", day_of_week="*"))
def weekly_reports():    
    # this should get called every hour by celery
    now = datetime.utcnow()
    reps = WeeklyReportSubscription.objects.filter(day_of_week=now.weekday()).filter(hours=now.hour)
    _run_reports(reps)
    
def _run_reports(reports):
    for report in reports:
        report.send()
