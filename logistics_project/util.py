from django.utils.translation.trans_real import translation


def translate(language, message):
    """
    In newer versions of Django, this is accomplished using the
    django.utils.translation.override context manager.

    We could write our own context manager, but this process mirrors
    the one used in rapidsms.messages.outgoing.
    """
    from rapidsms.lib.rapidsms.conf import settings as rapidsms_settings
    language = language or rapidsms_settings.LANGUAGE_CODE
    return translation(language).gettext(message)
