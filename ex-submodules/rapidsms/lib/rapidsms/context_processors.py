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
    try:
        site_title = settings.SITE_TITLE
    except AttributeError:
        warnings.warn("No SITE_TITLE specified in settings! rapidsms.context_processors.logo")
        site_title = "RapidSMS"
    try:
        base_template = settings.BASE_TEMPLATE
    except AttributeError:
        warnings.warn("No base_template specified in settings! rapidsms.context_processors.logo")
        base_template = "layout.html"

    try:
        base_template_split_2 = settings.BASE_TEMPLATE_SPLIT_2
    except AttributeError:
        base_template_split_2 = "layout-split-2.html"

    return {'logo_right_url' : logo_right_url ,
            'logo_left_url' : logo_left_url, 
            'site_title' : site_title,
            'base_template': base_template,
            'base_template_split_2': base_template_split_2 }