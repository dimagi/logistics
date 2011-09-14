from django.conf import settings
from rapidsms.utils.modules import try_import
import itertools
from models import Notification

def load_alert_generator(import_name):
    import_split = import_name.split('.')
    module_name = '.'.join(import_split[:-1])
    method_name = import_split[-1]

    module = try_import(module_name)
    if module is None:
        raise Exception("Alerts module %s is not defined." % (module_name))
    
    try:
        return getattr(module, method_name)
    except AttributeError:
        raise Exception("No function %s in module %s." % (method_name, module_name))

def get_alert_generators(type, *args, **kwargs):
    """
    Return a list of alert generators defined in the LOGISTICS_ALERT_GENERATORS
    setting.

    Return an empty list if no alert generators are defined.
    All exceptions raised while importing generators are
    allowed to propagate, to avoid masking errors.
    """

    try:
        registered_generators = getattr(settings, {
            'alert': 'LOGISTICS_ALERT_GENERATORS',
            'notif': 'LOGISTICS_NOTIF_GENERATORS',
        }[type])
    except AttributeError:
        # TODO: should this fail harder?
        registered_generators = []
        
    return [load_alert_generator(g)(*args, **kwargs) for g in registered_generators]

def get_notifications():
    return itertools.chain(*get_alert_generators('notif'))

def trigger_notifications():
    for notif in get_notifications():
        try:
            existing = Notification.objects.get(uid=notif.uid)
            #alert already generated
            #todo: add hook for amending or auto-dismissing alerts here (might not be the right place for auto-dismiss)?
            print 'alert already exists', notif.uid
        except Notification.DoesNotExist:
            #new alert; save to db
            notif.save()
            print 'new alert', notif
