from django.conf import settings


def logo(request):
    return {
        'logo_right_url' : settings.LOGO_RIGHT_URL ,
        'logo_left_url' : settings.LOGO_LEFT_URL,
        'site_title' : settings.SITE_TITLE,
        'base_template': settings.BASE_TEMPLATE,
        'base_template_split_2': settings.BASE_TEMPLATE_SPLIT_2
    }
