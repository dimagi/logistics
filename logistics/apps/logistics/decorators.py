from logistics.apps.malawi.const import Messages


def logistics_contact_required(f):
    """
    This decorator currently only works on an instance
    of a handler object. 
    """
    def require_logistics_contact(self, *args, **kwargs):
        if not hasattr(self.msg,'logistics_contact'):
            self.respond(Messages.REGISTRATION_REQUIRED_MESSAGE)
            # don't proceed with executing f
        else:
            return f(self, *args, **kwargs)
    
    return require_logistics_contact
