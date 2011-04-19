from django.db.models import signals
from django.conf import settings

def syncdb(app, created_models, verbosity=2, **kwargs):
    """Function used by syncdb signal"""
    loc_file = getattr(settings, "STATIC_LOCATIONS")
    if loc_file:
        app_name = app.__name__.rsplit('.', 1)[0]
        app_label = app_name.split('.')[-1]
        if app_label == "malawi":
            from logistics.apps.malawi.loader import init_static_data, load_locations
            init_static_data()
            load_locations(loc_file)
            
        
signals.post_syncdb.connect(syncdb)
