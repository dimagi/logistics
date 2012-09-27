from django import forms
from rapidsms.conf import settings
from rapidsms.models import Contact, Connection, Backend

def intl_clean_phone_number(phone_number):
    """
    * remove junk characters from a string representing a phone number
    * replaces optional domestic dialling code with intl dialling code
    * prefix with international dialling code (specified in settings.py)
    * RAISES: forms.ValidationError on invalid phone number
    """
    if not phone_number:
        return None
    cleaned = phone_number.strip()
    junk = [',', '-', ' ', '(', ')']
    for mark in junk:
        cleaned = cleaned.replace(mark, '')

    # replace domestic with intl dialling code, if domestic code defined
    idc = "%s%s" % (settings.INTL_DIALLING_CODE, settings.COUNTRY_DIALLING_CODE)
    try:
        ddc = str(settings.DOMESTIC_DIALLING_CODE)
        if cleaned.startswith(ddc):
            cleaned = "%s%s" % (idc, cleaned.lstrip(ddc))
            return cleaned
    except NameError:
        # ddc not defined, no biggie
        pass
    if cleaned.isdigit():
        return cleaned
    if cleaned.startswith(idc):
        return cleaned
    raise forms.ValidationError("Poorly formatted phone number. " + \
                                "Please enter the fully qualified number." + \
                                "Example: %(intl)s2121234567" % \
                                {'intl':idc})

def check_for_dupes(phone_number, contact=None):
    """
    return true if no dupes
    RAISES: forms.ValidationError if dupe connections are found
    """
    if not phone_number:
        return None
    if settings.DEFAULT_BACKEND:
        backend = Backend.objects.get(name=settings.DEFAULT_BACKEND)
    else:
        backend = Backend.objects.all()[0]
    dupes = Connection.objects.filter(identity=phone_number, 
                                      backend=backend)
    dupe_count = dupes.count()
    if dupe_count > 1:
        raise forms.ValidationError("Phone number already registered!")
    if dupe_count == 1:
        if dupes[0].contact is None:
            # this is fine, it just means we have a dangling connection
            # which we'll steal when we save
            pass
        # could be that we are editing an existing model
        elif dupes[0].contact != contact:
            raise forms.ValidationError("Phone number already registered to %s!" % dupes[0].contact)
    return True
