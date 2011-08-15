from django.test import TestCase
from scheduler.models import EventSchedule, ALL

class TestFields(TestCase):
    
    def testFields(self):
        schedule = EventSchedule(callback="foo", \
                                 minutes=ALL)
        args = ["a", 2, None]
        kwargs = {"foo": "bar", "4": None, "asdf": 18}
        schedule.callback_args = args
        schedule.callback_kwargs = kwargs
        schedule.save()
        
        sback = EventSchedule.objects.get(pk=schedule.pk)
        self.assertEqual(len(args), len(sback.callback_args))
        for i, val in enumerate(args):
            self.assertEqual(sback.callback_args[i], val)
        
        self.assertEqual(len(kwargs), len(sback.callback_kwargs))
        for k, val in kwargs.items():
            self.assertEqual(sback.callback_kwargs[k], val)
        
    def testDefaults(self):
        schedule = EventSchedule(callback="foo", minutes=ALL)
        schedule.save()
        sback = EventSchedule.objects.get(pk=schedule.pk)
        
        self.assertEqual(set(), sback.months)
        self.assertEqual(set(), sback.days_of_month)
        self.assertEqual(set(), sback.days_of_week)
        self.assertEqual(set(), sback.hours)
        self.assertEqual(set("*"), sback.minutes)
        
        