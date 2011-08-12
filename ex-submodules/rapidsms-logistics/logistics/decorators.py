from rapidsms.conf import settings
from logistics.util import config
from rapidsms.contrib.locations.models import Location

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
            elif settings.LOGISTICS_APPROVAL_REQUIRED and not self.msg.logistics_contact.is_approved:
                self.respond(config.Messages.APPROVAL_REQUIRED)
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
    
def return_if_place_not_set():
    def wrapper(f):
        def _return_if_place_not_set(request, *args, **kwargs):
            if not request.location:
                return None
            return f(request, *args, **kwargs)
        return _return_if_place_not_set
    return wrapper
    
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
