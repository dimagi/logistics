from django.conf import settings


def logo(request):
    return {
        'site_title' : settings.SITE_TITLE,
        'base_template': settings.BASE_TEMPLATE,
        'base_template_split_2': settings.BASE_TEMPLATE_SPLIT_2
    }
