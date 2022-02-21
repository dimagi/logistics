from django.test import TestCase
from datetime import datetime
from scheduler.decorators import businessday, businessday_before,\
    businessday_after, day
from scheduler.models import EventSchedule, ExecutionRecord, ALL_VALUE

def callback_func(arg=1):
    global callback_counter
    callback_counter = callback_counter + arg
    return callback_counter

def get_date():
    global global_date
    return global_date

def set_date(date):
    global global_date
    global_date = date

class TestDecorators(TestCase):
    
    def setUp(self):
        super(TestDecorators, self).setUp()
        global callback_counter
        callback_counter = 0
        
    def testDays(self):
        global callback_counter
        
        # the third is the first business day of october
        set_date(datetime(2011, 10, 1))
        
        @day(1, date_generator_func=get_date)
        def cb():
            return callback_func()
        
        @day(15, date_generator_func=get_date)
        def cb2():
            return callback_func()
        
        cb()
        self.assertEqual(1, callback_counter)
        cb()
        self.assertEqual(2, callback_counter)
        cb2()
        self.assertEqual(2, callback_counter)
        
        set_date(datetime(2011, 10, 15))
        
        cb()
        self.assertEqual(2, callback_counter)
        cb2()
        self.assertEqual(3, callback_counter)
        cb2()
        self.assertEqual(4, callback_counter)
    
        
    def testBusinessDays(self):
        global callback_counter
        
        # the third is the first business day of october
        set_date(datetime(2011, 10, 3))
        
        @businessday(1, date_generator_func=get_date)
        def cb():
            return callback_func()
        
        cb()
        self.assertEqual(1, callback_counter)
        cb()
        self.assertEqual(2, callback_counter)
        
        set_date(datetime(2011, 10, 1))
        cb()
        self.assertEqual(2, callback_counter)
        cb()
        self.assertEqual(2, callback_counter)
    
    def testBusinessDaysBefore(self):
        global callback_counter
        
        set_date(datetime(2011, 10, 14))
        
        @businessday_before(16, date_generator_func=get_date)
        def cb():
            return callback_func()
        
        cb()
        self.assertEqual(1, callback_counter)
        cb()
        self.assertEqual(2, callback_counter)
        
        set_date(datetime(2011, 10, 16))
        cb()
        self.assertEqual(2, callback_counter)
        cb()
        self.assertEqual(2, callback_counter)
    
    def testBusinessDaysAfter(self):
        global callback_counter
        
        set_date(datetime(2011, 10, 17))
        
        @businessday_after(15, date_generator_func=get_date)
        def cb():
            return callback_func()
        
        cb()
        self.assertEqual(1, callback_counter)
        cb()
        self.assertEqual(2, callback_counter)
        
        set_date(datetime(2011, 10, 15))
        cb()
        self.assertEqual(2, callback_counter)
        cb()
        self.assertEqual(2, callback_counter)


@businessday(1, date_generator_func=get_date)
def decorated_callback(arg=1):
    return callback_func(arg)

class testDecoratedExecution(TestCase):
    
    def setUp(self):
        super(testDecoratedExecution, self).setUp()
        global callback_counter
        callback_counter = 0
        EventSchedule.objects.all().delete()
        ExecutionRecord.objects.all().delete()
        schedule = EventSchedule(callback="scheduler.tests.decorators.decorated_callback", \
                                 minutes=ALL_VALUE)
        schedule.save()
        self.schedule = EventSchedule.objects.get(pk=schedule.pk)
        
        
    def testExecution(self):
        global callback_counter
        
        # the third is the first business day of october
        set_date(datetime(2011, 10, 3))
        self.assertEqual(0, callback_counter)
        self.assertEqual(1, self.schedule.execute())
        self.assertEqual(1, callback_counter)
        self.assertEqual(2, self.schedule.execute())
        self.assertEqual(2, callback_counter)
        
        set_date(datetime(2011, 10, 1))
        self.schedule.execute()
        self.assertEqual(2, callback_counter)
        self.schedule.execute()
        self.assertEqual(2, callback_counter)