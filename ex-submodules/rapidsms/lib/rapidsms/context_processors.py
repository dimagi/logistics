from django.conf import settings
import warnings
def logo(request):
    try:
        logo_right_url = settings.LOGO_RIGHT_URL
        logo_left_url = settings.LOGO_LEFT_URL
    except AttributeError:
        warnings.warn("No LOGO_LEFT_URL and/or LOGO_RIGHT_URL specified in settings! rapidsms.context_processors.logo")
        logo_right_url = ""
        logo_left_url = ""

    return {'logo_right_url' : logo_right_url ,
            'logo_left_url' : logo_left_url }
