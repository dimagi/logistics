from django.test import TestCase
from datetime import datetime
from scheduler.models import EventSchedule, ALL, ExecutionRecord
import logging

def callback_func(arg=1):
    global callback_counter
    logging.info("adding %s to global_var (%s)" % (arg, callback_counter))
    callback_counter = callback_counter + arg
    return callback_counter

class TestExecution(TestCase):
    
    def setUp(self):
        super(TestExecution, self).setUp()
        global callback_counter
        callback_counter = 0
        EventSchedule.objects.all().delete()
        ExecutionRecord.objects.all().delete()
        schedule = EventSchedule(callback="scheduler.tests.execution.callback_func", \
                                 minutes=ALL)
        schedule.save()
        self.schedule = EventSchedule.objects.get(pk=schedule.pk)
        self.assertTrue(self.schedule.last_ran is None)
        
    def testExecution(self):
        self.assertEqual(1, self.schedule.execute())
        self.assertEqual(2, self.schedule.execute())
    
    def testArgs(self):
        self.assertEqual(1, self.schedule.execute())
        self.schedule.callback_args = [5]
        self.schedule.save()
        self.assertEqual(6, self.schedule.execute())
        self.assertEqual(11, self.schedule.execute())
    
    def testKwargs(self):
        self.assertEqual(1, self.schedule.execute())
        self.schedule.callback_kwargs = {"arg": 3}
        self.schedule.save()
        self.assertEqual(4, self.schedule.execute())
        self.assertEqual(7, self.schedule.execute())
    
    def testExecutionUpdates(self):
        self.assertEqual(0, ExecutionRecord.objects.count())
        asof = datetime.utcnow()
        self.assertEqual(1, self.schedule.run(asof))
        self.schedule = EventSchedule.objects.get(pk=self.schedule.pk)
        self.assertEqual(asof, self.schedule.last_ran)
        self.assertEqual(1, ExecutionRecord.objects.count())
        [rec] = ExecutionRecord.objects.all()
        self.assertEqual(self.schedule, rec.schedule)
        self.assertEqual(asof, rec.runtime)