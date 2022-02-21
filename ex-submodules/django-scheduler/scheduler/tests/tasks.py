from django.test import TestCase
from scheduler.models import EventSchedule, ExecutionRecord, ALL_VALUE
import logging
from scheduler.tasks import scheduler_heartbeat

def callback_func(arg=1):
    global callback_counter
    logging.info("adding %s to global_var (%s)" % (arg, callback_counter))
    callback_counter = callback_counter + arg
    return callback_counter

class TestTasks(TestCase):
    
    def setUp(self):
        super(TestTasks, self).setUp()
        global callback_counter
        callback_counter = 0
        EventSchedule.objects.all().delete()
        ExecutionRecord.objects.all().delete()
        schedule = EventSchedule(callback="scheduler.tests.tasks.callback_func", \
                                 minutes=ALL_VALUE)
        schedule.save()
        self.schedule = EventSchedule.objects.get(pk=schedule.pk)
        self.assertTrue(self.schedule.last_ran is None)
        
    def testTasks(self):
        global callback_counter
        self.assertEqual(0, callback_counter)
        scheduler_heartbeat()
        self.assertEqual(1, callback_counter)
        scheduler_heartbeat()
        self.assertEqual(2, callback_counter)
