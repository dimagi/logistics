from django.conf import settings
from django.utils.importlib import import_module
from datetime import datetime, timedelta, time

if hasattr(settings,'LOGISTICS_CONFIG'):
    config = import_module(settings.LOGISTICS_CONFIG)
else:
    import config

DEFAULT_DATE_FORMAT = "%m/%d/%Y"
    
class DateSpan(object):
    """
    A useful class for representing a date span
    """
    
    def __init__(self, startdate, enddate, format=DEFAULT_DATE_FORMAT, 
                 display_format=None):
        self.startdate = startdate
        self.enddate = enddate
        self.format = format
        self.display_format = format if display_format is None else display_format
    
    @property
    def startdate_param(self):
        if self.startdate:
            return self.startdate.strftime(self.format)
    
    @property
    def enddate_param(self):
        if self.enddate:
            return self.enddate.strftime(self.format)
        
    
    def is_valid(self):
        # this is a bit backwards but keeps the logic in one place
        return not bool(self.get_validation_reason())
    
    def get_validation_reason(self):
        if self.startdate is None or self.enddate is None:
            return "You have to specify both dates!"
        else:
            if self.enddate < self.startdate:
                return "You can't have an end date of %s after start date of %s" % (self.enddate, self.startdate)
        return ""
    
    def __str__(self):
        # if the end date is today or tomorrow, use "last N days syntax"  
        today = datetime.combine(datetime.today(), time())
        day_after_tomorrow = today + timedelta (days=2)
        if today <= self.enddate < day_after_tomorrow:
            return "last %s days" % (self.enddate - self.startdate).days 
        return "%s to %s" % (self.startdate.strftime(self.display_format), 
                             self.enddate.strftime(self.display_format))
        
    @classmethod
    def since(cls, days, format=DEFAULT_DATE_FORMAT, display_format=None):
        tomorrow = datetime.utcnow() + timedelta(days=1)
        end = datetime(tomorrow.year, tomorrow.month, tomorrow.day)
        start = end - timedelta(days=days)
        return DateSpan(start, end, format, display_format)
                    
    
