from django.db.models import signals
from django.conf import settings

def syncdb(app, created_models, verbosity=2, **kwargs):
    """Function used by syncdb signal"""
    app_name = app.__name__.rsplit('.', 1)[0]
    app_label = app_name.split('.')[-1]
    if app_label == "malawi":
        load_static_data()

def load_static_data():
    from logistics.apps.malawi.loader import init_static_data, load_locations, load_products
    init_static_data()
    loc_file = getattr(settings, "STATIC_LOCATIONS")
    if loc_file:
        load_locations(loc_file)
    product_file = getattr(settings, "STATIC_PRODUCTS")
    if product_file:
        load_products(product_file)

if hasattr(settings, 'LOGISTICS_AUTOLOAD_DATA'):
    if settings.LOGISTICS_AUTOLOAD_DATA:
        signals.post_syncdb.connect(syncdb)
