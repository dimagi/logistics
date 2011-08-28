from django.http import HttpResponseForbidden
from django.conf import settings

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
