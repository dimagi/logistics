"""

"""
import time
import logging
from datetime import datetime, timedelta, MINYEAR
from rapidsms.tests.scripted import TestScript
import rapidsms.contrib.scheduler.app as scheduler_app
from rapidsms.contrib.scheduler.models import EventSchedule, ALL

start = datetime(MINYEAR, 1, 1, 0, 0, 0, 0 , tzinfo=None)
sec = timedelta(seconds=1)
min = timedelta(minutes=1)
hour = timedelta(hours=1)
day = timedelta(days=1)
week = timedelta(weeks=1)
month = timedelta(days=31) #close enough


class TestSchedule (TestScript):
    apps = ([scheduler_app.App])
    
    def setUp(self):
        TestScript.setUp(self)
        EventSchedule.objects.all().delete()

    def test_all(self):
        schedule = EventSchedule(callback="foo", \
                                 minutes=ALL)
        self.assertTrue(schedule.should_fire(start))
        self.assertTrue(schedule.should_fire(start+sec))
        self.assertTrue(schedule.should_fire(start+min))
        self.assertTrue(schedule.should_fire(start+hour))
        self.assertTrue(schedule.should_fire(start+day))
        self.assertTrue(schedule.should_fire(start+week))
        self.assertTrue(schedule.should_fire(start+sec+min+hour+day+week))
            
    def tearDown(self):
        pass
