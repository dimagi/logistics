#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from datetime import datetime
from django.db import models
from django.utils.dates import MONTHS, WEEKDAYS_ABBR
from scheduler.fields import JSONField
import logging

# set timespans (e.g. EventSchedule.hours, EventSchedule.minutes) to 
# ALL when we want to schedule something for every hour/minute/etc.
ALL = '*'
ALL_VALUE = ['*']
# knowing which fields are related to time is useful
# for a bunch of operations below
# TIME_FIELDS should always reflect the names of 
# the sets of numbers which determine the scheduled time
_TIME_FIELDS = ['minutes', 'hours', 'days_of_week', 
               'days_of_month', 'months']


class ExecutionRecord(models.Model):
    """
    Each time a scheduler fires, a record is kept for historical/auditing 
    purposes
    """
    
    schedule = models.ForeignKey("EventSchedule")
    runtime = models.DateTimeField()

class FailedExecutionRecord(ExecutionRecord):
    """
    Execution record for failures.
    """
    message = models.TextField()

class EventSchedule(models.Model):
    """ 
    Create a new EventSchedule and save it every time 
    you want to register a new event on a schedule
    we can implement one_off future events by setting count to 1 
    All timespans less than the specified one must be set
    i.e. a weekly schedule must also specify which hour, minute, etc.
    However, all timespans greater than the specified one
    default to "all" (as long as one is specified).
    i.e. a weekly schedule will fire every month
    
    callback - all callback function must take as the first 
        argument a reference to a 'router' object
    """
    callback = models.CharField(max_length=255, 
                                help_text="Name of Python callback function")
    
    description = models.CharField(max_length=255, null=True, blank=True)

    # a list
    callback_args = JSONField(null=True, blank=True)
    # a dictionary
    callback_kwargs = JSONField(null=True, blank=True)
    
    # the following are sets of numbers
    months = JSONField(null=True, blank=True, help_text="'1,2,3' for jan, feb, march - '*' for all")
    days_of_month = JSONField(null=True, blank=True, help_text="'1,2,3' for 1st, 2nd, 3rd - '*' for all")
    days_of_week = JSONField(null=True, blank=True, help_text="'0,1,2' for mon, tue, wed - '*' for all")
    hours = JSONField(null=True, blank=True, help_text="'0,1,2' for midnight, 1 o'clock, 2 - '*' for all")
    minutes = JSONField(null=True, blank=True, help_text="'0,1,2' for X:00, X:01, X:02 - '*' for all")
    
    start_time = models.DateTimeField(null=True, blank=True, 
                                      help_text="When do you want alerts to start? Leave blank for 'now'.")
    end_time = models.DateTimeField(null=True, blank=True, 
                                      help_text="When do you want alerts to end? Leave blank for 'never'.")
    last_ran = models.DateTimeField(null=True) # updated each time the scheduler runs
    
    # how many times do we want this event to fire? optional
    count = models.IntegerField(null=True, blank=True, 
                                help_text="How many times do you want this to fire? Leave blank for 'continuously'")
    
    # whether this schedule is active or not
    active = models.BooleanField(default=True)
    
    # First, we must define some utility classes
    class AllMatch(set):
        """Universal set - match everything"""
        def __contains__(self, item): return True
    allMatch = AllMatch(['*'])

    class UndefinedSchedule(TypeError):
        """ raise this error when attempting to save a schedule with a
        greater timespan specified without specifying the lesser timespans
        i.e. scheduling an event for every hour without specifying what
        minute
        """
        pass

    def __str__(self):
        return unicode(self).encode('utf-8')
    
    def __unicode__(self):
        def _list_to_string(list, conversion_dict=None):
            if len(list)>0:
                if conversion_dict is not None:
                    return ", ".join( [unicode(conversion_dict[m]) for m in list] )
                else:
                    return ", ".join( [unicode(m) for m in list] )
            else: 
                return 'All'
        months = _list_to_string(self.months, MONTHS)
        days_of_month = _list_to_string(self.days_of_month)
        days_of_week = _list_to_string(self.days_of_week, WEEKDAYS_ABBR)
        hours = _list_to_string(self.hours)
        minutes = _list_to_string(self.minutes)
        return "%s: Months:(%s), Days of Month:(%s), Days of Week:(%s), Hours:(%s), Minutes:(%s)" % \
            ( self.callback, months, days_of_month, days_of_week, hours, minutes )
            
    def __init__(self, *args, **kwargs):
        super(EventSchedule, self).__init__(*args, **kwargs)
        if self.callback_args is None: self.callback_args = []
        if self.callback_kwargs is None: self.callback_kwargs = {}
        for time in _TIME_FIELDS:
            if getattr(self, time) is None: 
                setattr(self,time, [])
    
    @staticmethod
    def validate(months, days_of_month, days_of_week, hours, minutes):
        """
        The following function doesn't touch data: it just checks 
        for valid boundaries
        
        when a timespan is set, all sub-timespans must also be set
        i.e. when a weekly schedule is set, one must also specify day, hour, and minute.
        """
        EventSchedule.validate_ranges(months, days_of_month, days_of_week, hours, minutes)
        EventSchedule.validate_subtimespans(months, days_of_month, days_of_week, hours, minutes)
        
    @staticmethod
    def validate_ranges(months, days_of_month, days_of_week, hours, minutes):
        EventSchedule.check_minutes_bounds(minutes)
        EventSchedule.check_hours_bounds(hours)
        EventSchedule.check_days_of_week_bounds(days_of_week)
        EventSchedule.check_days_of_month_bounds(days_of_month)
        EventSchedule.check_months_bounds(months)
    
    @staticmethod
    def validate_subtimespans(months, days_of_month, days_of_week, hours, minutes):
        if len(minutes)==0 and len(hours)==0 and len(days_of_week)==0 and \
            len(days_of_month)==0 and len(months)==0:
            raise TypeError("Must specify a time interval for schedule")
        if len(hours)>0 and len(minutes)==0:
            raise EventSchedule.UndefinedSchedule("Must specify minute(s)")
        if len(days_of_week)>0 and len(hours)==0: 
            raise EventSchedule.UndefinedSchedule("Must specify hour(s)")
        if len(days_of_month)>0 and len(hours)==0: 
            raise EventSchedule.UndefinedSchedule("Must specify hour(s)")
        if len(months)>0 and len(days_of_month)==0 and len(days_of_week)==0:
            raise EventSchedule.UndefinedSchedule("Must specify day(s)")

    # we break these out so we can reuse them in forms.py        
    @staticmethod
    def check_minutes_bounds(minutes):
        check_bounds('Minutes', minutes, 0, 59)
    @staticmethod
    def check_hours_bounds(hours):
        check_bounds('Hours', hours, 0, 23)
    @staticmethod
    def check_days_of_week_bounds(days_of_week):
        check_bounds('Days of Week', days_of_week, 0, 6)
    @staticmethod
    def check_days_of_month_bounds(days_of_month):
        check_bounds('Days of Month', days_of_month, 1, 31)
    @staticmethod
    def check_months_bounds(months):
        check_bounds('Months', months, 1, 12)
        
    def save(self, *args, **kwargs):
        # transform all the input into known data structures
        for time in _TIME_FIELDS:
            val = getattr(self, time)
            if val is None or len(val)==0:
                # set default value to empty list
                setattr(self,time,[])
            if isinstance(val,list):
                # accept either lists or sets, but turn all lists into 
                setattr(self,time,val)
            if not self._valid(getattr(self,time)):
                raise TypeError("%s must be specified as " % time + 
                                "lists of numbers, an empty list, or '*'")
        
        # validate those data structures
        self.validate(self.months, self.days_of_month, self.days_of_week, 
                      self.hours, self.minutes)
        
        super(EventSchedule, self).save(*args, **kwargs)
    
    def should_fire(self, when):
        """Return True if this event should trigger at the specified datetime """
        if self.start_time:
            if self.start_time > when:
                return False
        if self.end_time:
            if self.end_time < when:
                return False
            
        # The internal variables in this function are because allMatch doesn't 
        # pickle well. This would be alleviated if this functionality were optimized
        # to stop doing db calls on every fire
        minutes = self.minutes
        hours = self.hours
        days_of_week = self.days_of_week
        days_of_month = self.days_of_month
        months = self.months
        if self.minutes == ALL_VALUE: minutes = self.allMatch
        if self.hours == ALL_VALUE: hours = self.allMatch
        if self.days_of_week == ALL_VALUE: days_of_week = self.allMatch
        if self.days_of_month == ALL_VALUE: days_of_month = self.allMatch
        if self.months == ALL_VALUE: months = self.allMatch
        
        # when a timespan is set, all super-timespans default to 'all'
        # i.e. a schedule specified for hourly will automatically be sent
        # every day, week, and month.
        if len(months) == 0:
            months=self.allMatch
        if months == self.allMatch:
            if len(days_of_month)==0:
                days_of_month = self.allMatch
            if len(days_of_week)==0:
                days_of_week = self.allMatch
        if len(hours) == 0 and days_of_month==self.allMatch and \
            days_of_week == self.allMatch:
            hours = self.allMatch
        # self.minutes will never be empty
        
        # the following ensures that 'days of month' will override empty 'day of week'
        # and vice versa
        if len(days_of_month)>0 and len(days_of_week)==0:
            days_of_week = self.allMatch
        if len(days_of_week)>0 and len(days_of_month)==0:
            days_of_month = self.allMatch
        
        return ((when.minute     in minutes) and
                (when.hour       in hours) and
                (when.day        in days_of_month) and
                (when.weekday()  in days_of_week) and
                (when.month      in months))

    def activate(self):
        self.active = True
        self.save()
        
    def deactivate(self):
        self.active = False
        self.save()

    def _valid(self, timespan):
        if isinstance(timespan, list) or timespan == '*':
            return True
        return False

    def execute(self):
        """
        Executes the referenced function and returns the results
        """
        # TODO: make this less brittle if imports or args don't line up
        module, callback = self.callback.rsplit(".", 1)
        module = __import__(module, globals(), locals(), [callback])
        callback = getattr(module, callback)
        args = self.callback_args or []
        kwargs = self.callback_kwargs or {}
        return callback(*args, **kwargs)
        
    def _record_execution(self, asof):
        if self.count:
            self.count = self.count - 1
            # should we delete expired schedules? we do now.
            if self.count <= 0: 
                self.active = False
        # should we delete expired schedules? we do now.
        if self.end_time:
            if asof > self.end_time:
                self.active = False
        self.last_ran = asof
        self.save()
        
    def record_execution(self, asof):
        self._record_execution(asof)
        ExecutionRecord.objects.create(schedule=self,
                                       runtime=asof)
    
    def record_failed_execution(self, asof, msg):
        self._record_execution(asof)
        FailedExecutionRecord.objects.create(schedule=self,
                                             runtime=asof, 
                                             message=msg)
        
    def run(self, asof):
        """
        Runs the schedule, update the model appropriately, return the results. 
        """
        try:
            ret = self.execute()
        except Exception, e:
            logging.exception("Problem executing scheduled item %s" % self)
            self.record_failed_execution(asof, str(e))
            return None
        self.record_execution(asof)
        return ret

    
############################
# global utility functions #
############################

def check_bounds(name, time_set, min, max):
    if time_set != ALL_VALUE: # ignore AllMatch/'*'
        for m in time_set: # check all values in set
            if int(m) < min or int(m) > max:
                raise TypeError("%s (%s) must be a value between %s and %s" % \
                                (name, m, min, max))
