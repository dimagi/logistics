from datetime import datetime, timedelta
from django.http import HttpRequest
from logistics.apps.logistics.util import config
from rapidsms.contrib.locations.models import Location
from logistics.apps.logistics.reports import DateSpan

def logistics_contact_required():
    """
    This decorator currently only works on an instance
    of a handler object. 
    """
    def wrapper(f):
        def require_logistics_contact(self, *args, **kwargs):
            if not hasattr(self.msg,'logistics_contact'):
                self.respond(config.Messages.REGISTRATION_REQUIRED_MESSAGE)
                # don't proceed with executing f
            else:
                return f(self, *args, **kwargs)
        return require_logistics_contact
    return wrapper

def logistics_permission_required(operation):
    """
    This decorator currently only works on an instance
    of a handler object. It also assumes that 
    logistics_contact_required has already been run.
    """
    def wrapper(f):
        def require_role(self, *args, **kwargs):
            if not config.has_permissions_to(self.msg.logistics_contact, operation):
                self.respond(config.Messages.UNSUPPORTED_OPERATION)
            else:
                return f(self, *args, **kwargs)
        return require_role
    return wrapper

def logistics_contact_and_permission_required(operation):
    """
    This decorator currently only works on an instance
    of a handler object. 
    """
    def both(f):
        return logistics_contact_required()(logistics_permission_required(operation)(f)) # yikes
    return both
    
def place_in_request(param="place"):
    """
    Expects a parameter in the request, and if found, will
    populate request.location with an instance of that 
    place, by code.
    """
    def wrapper(f):
        def put_place_on_request(request, *args, **kwargs):
            code = request.GET.get(param, None)
            if code:
                request.location = Location.objects.get(code=code)
            else:
                request.location = None
            request.select_location = True # used in the templates
            return f(request, *args, **kwargs)
        return put_place_on_request
    return wrapper


def datespan_in_request(from_param="from", to_param="to", format_string="%m/%d/%Y"):
    """
    Wraps a request with dates based on url params or defaults and
    Checks date validity.
    """
    # this is loosely modeled after example number 4 of decorator
    # usage here: http://www.python.org/dev/peps/pep-0318/
    def get_dates(f):
        def wrapped_func(*args, **kwargs):
            # attempt to find the request object from all the argument
            # values, checking first the args and then the kwargs 
            req = None
            for arg in args:
                if _is_http_request(arg):
                    req = arg
                    break
            if not req:
                for arg in kwargs.values():
                    if _is_http_request(arg):
                        req = arg
                        break
            if req:
                dict = req.POST if req.method == "POST" else req.GET
                def date_or_nothing(param):
                    return datetime.strptime(dict[param], format_string)\
                             if param in dict and dict[param] else None
                startdate = date_or_nothing(from_param)
                enddate = date_or_nothing(to_param)
                if startdate or enddate:
                    req.datespan = DateSpan(startdate, enddate, format_string)
                else:        
                    # default to the last 30 days
                    req.datespan = DateSpan.since(30)
                    
            return f(*args, **kwargs) 
        if hasattr(f, "func_name"):
            wrapped_func.func_name = f.func_name
            # preserve doc strings
            wrapped_func.__doc__ = f.__doc__  
            
            return wrapped_func
        else:
            # this means it wasn't actually a view.  
            return f 
    return get_dates

def _is_http_request(obj):
    return obj and isinstance(obj, HttpRequest)