from scheduler.models import EventSchedule

def get_relevant_schedules(asof):
    """
    Get all schedules relevant given a datetime object.
    
    Relevant implies they are currently active, that the "active"
    status checks that they haven't already been run in this "active" 
    period.
    """
    # todo, use the last_run field as well
    return [s for s in EventSchedule.objects.filter(active=True) \
            if s.should_fire(asof)]
    
def create_monthly_event(callback, day, hour, minute, callback_args=None):
    # relies on all the built-in checks in EventSchedule.save()
    schedule = EventSchedule(callback=callback, hours=set([hour]), \
                             days_of_month=set([day]), minutes=set([minute]), \
                             callback_args=callback_args )
    schedule.save()
    return schedule

def create_weekly_event(callback, day, hour, minute, callback_args=None):
    # relies on all the built-in checks in EventSchedule.save()
    schedule = EventSchedule(callback=callback, hours=set([hour]), \
                             days_of_week=set([day]), minutes=set([minute]), \
                             callback_args=callback_args )
    schedule.save()
    return schedule

def create_daily_event(callback, hour, minute, callback_args):
    # relies on all the built-in checks in EventSchedule.save()
    schedule = EventSchedule(callback=callback, hours=set([hour]), \
                             minutes=set([minute]), \
                             callback_args=callback_args )
    schedule.save()
    return schedule
