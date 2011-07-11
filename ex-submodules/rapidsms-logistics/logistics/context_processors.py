from django.conf import settings

def custom_settings(request):
    return {"excel_export": settings.LOGISTICS_EXCEL_EXPORT_ENABLED,
            "%s_hack" % settings.COUNTRY: True}

def google_analytics(request):
    return {"GOOGLE_ANALYTICS_ID": getattr(settings, 'GOOGLE_ANALYTICS_ID', None)}
