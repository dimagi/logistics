from django.conf import settings
from django.utils.importlib import import_module

if hasattr(settings,'LOGISTICS_CONFIG'):
    config = import_module(settings.LOGISTICS_CONFIG)
else:
    import config
