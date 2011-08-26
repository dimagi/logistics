from django.utils.translation import ugettext as _
from rapidsms.conf import settings

def language_in_request(request):
    if request.LANGUAGE_CODE and request.LANGUAGE_CODE in dict(settings.LANGUAGES):
        return {"language": _(dict(settings.LANGUAGES)[request.LANGUAGE_CODE])}
    return {"language": _(settings.LANGUAGES[0][1])}
    