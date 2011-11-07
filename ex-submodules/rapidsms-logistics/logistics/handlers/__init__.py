from rapidsms.conf import settings

def logistics_keyword(kw):
    if settings.LOGISTICS_USE_DEFAULT_HANDLERS:
        return kw
    return "thiscrazyhackylongkeywordshouldhopefullynevermatchanyintentionalsms"
