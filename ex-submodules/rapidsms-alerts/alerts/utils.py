from django.conf import settings
import itertools
from models import Notification, NotificationComment
from importutil import dynamic_import

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
        
    return [dynamic_import(g)(*args, **kwargs) for g in registered_generators]

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
            notif.initialize()
            notif.save()
            print 'new alert', notif
            #'created' comment
            comment = NotificationComment(notification=notif, user=None, text='notification created')
            comment.save()
