from django.utils.importlib import import_module
from rapidsms.conf import settings

if hasattr(settings,'LOGISTICS_CONFIG'):
    config = import_module(settings.LOGISTICS_CONFIG)
else:
    import config