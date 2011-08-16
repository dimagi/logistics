from django.conf import settings

# use rapidsms 
USE_RAPIDSMS = getattr(settings, "USE_RAPIDSMS", False)
