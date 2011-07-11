from django.conf import settings

def custom_settings(request):
    return {"excel_export": settings.LOGISTICS_EXCEL_EXPORT_ENABLED,
            "%s_hack" % settings.COUNTRY: True}

def google_analytics(request):
    return {"GOOGLE_ANALYTICS_ID": getattr(settings, 'GOOGLE_ANALYTICS_ID', None)}

def base_template(request):
    """ 
    For compatibility with the logistics app, which allows users
    to specify a custom 'base template' dynamically
    """ 
    try:
        base_template = settings.BASE_TEMPLATE
    except AttributeError:
        base_template = "layout.html"

    try:
        base_template_split_2 = settings.BASE_TEMPLATE_SPLIT_2
    except AttributeError:
        base_template_split_2 = "layout-split-2.html"

    return {'base_template': base_template,
            'base_template_split_2': base_template_split_2 }
