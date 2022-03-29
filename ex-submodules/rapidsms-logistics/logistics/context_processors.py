from __future__ import unicode_literals
from rapidsms.conf import settings


def custom_settings(request):
    return {
        "STATIC_URL": settings.STATIC_URL,
        "excel_export": settings.LOGISTICS_EXCEL_EXPORT_ENABLED,
        "%s_hack" % settings.COUNTRY: True
    }


def user_profile(request):
    from logistics_project.apps.malawi.util import get_user_profile
    return {
        'logistics_user_profile': get_user_profile(request.user)
    }
