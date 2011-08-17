from datetime import datetime, date
from dimagi.utils.dates import get_business_day_of_month,\
    get_business_day_of_month_after, get_business_day_of_month_before,\
    get_day_of_month

def day(day, date_generator_func=datetime.utcnow):
    """
    Allows you to define a method, for which calling it will be
    a noop unless the day is the Nth day of the month (negative 
    numbers accepted).
    
    You can pass in date_generator_func to use dates other than
    today (defined in utc). It should return a datetime object.
    """
    def wrapper(f):
        def check_day(*args, **kwargs):
            comp = date_generator_func()
            appropriate_day = get_day_of_month(comp.year, comp.month, day)
            if comp.date() == appropriate_day:
                return f(*args, **kwargs)
            else:
                pass
        return check_day
    return wrapper


def businessday(day, date_generator_func=datetime.utcnow):
    """
    Allows you to define a method, for which calling it will be
    a noop unless the day is the Nth business day of the month 
    (negative numbers accepted).
    
    You can pass in date_generator_func to use dates other than
    today (defined in utc). It should return a datetime object.
    """
    def wrapper(f):
        def check_day(*args, **kwargs):
            comp = date_generator_func()
            appropriate_day = get_business_day_of_month(comp.year, comp.month, day)
            if comp.date() == appropriate_day:
                return f(*args, **kwargs)
            else:
                pass
        return check_day
    return wrapper

def businessday_after(day, date_generator_func=datetime.utcnow):
    """
    Allows you to define a method, for which calling it will be
    a noop unless the day is the first business day on or after 
    the day of month specified
    
    You can pass in date_generator_func to use dates other than
    today (defined in utc)
    """
    def wrapper(f):
        def check_day(*args, **kwargs):
            comp = date_generator_func()
            appropriate_day = get_business_day_of_month_after(comp.year, comp.month, day)
            if comp.date() == appropriate_day:
                return f(*args, **kwargs)
            else:
                pass
        return check_day
    return wrapper

def businessday_before(day, date_generator_func=datetime.utcnow):
    """
    Allows you to define a method, for which calling it will be
    a noop unless the day is the first business day on or before
    the day of month specified.
    
    You can pass in date_generator_func to use dates other than
    today (defined in utc)
    """
    def wrapper(f):
        def check_day(*args, **kwargs):
            comp = date_generator_func()
            appropriate_day = get_business_day_of_month_before(comp.year, comp.month, day)
            if comp.date() == appropriate_day:
                return f(*args, **kwargs)
            else:
                pass
        return check_day
    return wrapper
