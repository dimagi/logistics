from django.http import HttpResponseForbidden
from django.conf import settings
from logistics.util import config


def magic_token_required():
    """
    Use a magic token in the settings for fake authentication. 
    Useful for API views. Will also allow access if a valid session
    exists.
    """
    def wrapper(f):
        def require_magic_token(request, *args, **kwargs):
            user = request.user
            if user.is_authenticated() and user.is_active or \
               "magic_token" in request.REQUEST and request.REQUEST["magic_token"] == settings.MAGIC_TOKEN:
                return f(request, *args, **kwargs)
            return HttpResponseForbidden("You have to be logged in or have the magic token to do that!")
        return require_magic_token
    return wrapper


def require_facility(f):
    """
    Meant to decorate the handle() method of an SMS handler.
    Checks to make sure that the contact's supply point is a facility.
    Assumes that self.msg.logistics_contact exists.
    """
    def inner(self, *args, **kwargs):
        if (
            self.msg.logistics_contact.supply_point and
            self.msg.logistics_contact.supply_point.type.code == config.SupplyPointCodes.FACILITY
        ):
            return f(self, *args, **kwargs)

        self.respond(config.Messages.ERROR_NO_FACILITY_ASSOCIATION)
    return inner


def require_district(f):
    """
    Meant to decorate the handle() method of an SMS handler.
    Checks to make sure that the contact's supply point is a district.
    Assumes that self.msg.logistics_contact exists.
    """
    def inner(self, *args, **kwargs):
        if (
            self.msg.logistics_contact.supply_point and
            self.msg.logistics_contact.supply_point.type.code == config.SupplyPointCodes.DISTRICT
        ):
            return f(self, *args, **kwargs)

        self.respond(config.Messages.ERROR_NO_DISTRICT_ASSOCIATION)
    return inner


def validate_base_level(allowed_base_levels):
    """
    This decorator currently only works on an instance of a handler
    object. It also assumes that self.msg.logistics_contact exists
    (which is true if the logistics_contact_required decorator has
    already been run).

    If validation passes, a base_level attribute is also added to the
    handler.

    :param allowed_base_levels: a list of the base levels to allow;
    for example, [BaseLevel.HSA, BaseLevel.FACILITY]
    """
    def wrapper(f):
        def inner(self, *args, **kwargs):
            base_level = None
            supply_point = self.msg.logistics_contact.supply_point

            if supply_point:
                if supply_point.type_id == config.SupplyPointCodes.HSA:
                    base_level = config.BaseLevel.HSA
                elif supply_point.type_id == config.SupplyPointCodes.FACILITY:
                    base_level = config.BaseLevel.FACILITY

            if base_level not in allowed_base_levels:
                self.respond(config.Messages.UNSUPPORTED_OPERATION)
            else:
                self.base_level = base_level
                return f(self, *args, **kwargs)
        return inner
    return wrapper
