""" This is where we actually schedule when and how often reports get run """

from datetime import datetime
from celery.schedules import crontab
from celery.decorators import periodic_task
from scheduler.schedules import get_relevant_schedules
import logging

@periodic_task(run_every=crontab(hour="*", minute="*", day_of_week="*"))
def scheduler_heartbeat():
    """
    Check all scheduled tasks and run whatever is necessary.
    """
    # this should get called every minute by celery
    currtime = datetime.utcnow()
    relevant = get_relevant_schedules(currtime)
    for schedule in relevant:
        try:
            # call the callback function
            # possibly passing in args and kwargs
            schedule.run(currtime)
        except Exception:
            # Don't prevent exceptions from killing the rest
            logging.exception("Problem in the scheduler heartbeat for %s" % schedule)            