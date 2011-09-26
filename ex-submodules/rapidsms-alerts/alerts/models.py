from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.utils.dateformat import format as format_date

NOTIF_STATUS = (
    ('new', 'new'),
    ('fu', 'following up'),
    ('esc', 'escalated'),
    ('closed', 'resolved'),
)

class Notification(models.Model):
    uid = models.CharField(max_length=256)
    created_on = models.DateTimeField(auto_now_add=True)

    text = models.TextField()
    url = models.TextField(null=True, blank=True)
    alert_type = models.CharField(max_length=256) #fully-qualified python name of the corresponding AlertType class

    owner = models.ForeignKey(User, null=True, blank=True)
    status = models.CharField(max_length=10, choices=NOTIF_STATUS, default='new')

    def json(self, user=None):
        return {
            'id': self.id,
            'msg': self.text,
            'url': self.url,
            'owner': user_name(self.owner),
            'status': self.status,
            'comments': [cmt.json() for cmt in self.comments.all()],
            'actions': self.actions(user),
        }

    def actions(self, user):
        """return the actions this user may currently take on this alert"""
        if self.status == 'closed':
            return []
        elif user == self.owner and self.status == 'fu':
            return ['resolve']
        #escalation stuff not finalized; just for testing purposes now
        elif self.status == 'esc':
            return ['fu', 'resolve']
        else:
            return ['fu', 'esc', 'resolve']

    def __unicode__(self):
        return unicode(self.__dict__)

    @property
    def _type(self):
        if not hasattr(self, '_type_inst'):
            from alerts.utils import dynamic_import #warning: circular import! should fix this
            self._type_inst = dynamic_import(self.alert_type)(self)
        return self._type_inst

    def __getattribute__(self, name):
        """delegate out to the associated AlertType; in practice, this will only be done for
        known methods in the AlertType interface"""
        try:
            return super(Notification, self).__getattribute__(name)
        except AttributeError:
            if name in dir(self._type) and not name.startswith('_'):
                return getattr(self._type, name)
            else:
                raise

class NotificationComment(models.Model):
    notification = models.ForeignKey(Notification, related_name='comments')
    user = models.ForeignKey(User, null=True, blank=True) #no user is for system-generated entries
    date = models.DateTimeField(auto_now_add=True)
    text = models.TextField()

    def json(self):
        return {
            'text': self.text,
            'date_fmt': format_date(self.date, 'M j, H:i'),
            'author': user_name(self.user, default=settings.SYSTEM_USERNAME),
            'is_system': self.user is None,
        }

    def __unicode__(self):
        return unicode(self.__dict__)

def user_name(user, default=None):
    if user is None:
        return default
    else:
        fname = user.first_name
        lname = user.last_name
        return '%s %s' % (fname, lname) if fname and lname else user.username

class ResolutionAcknowledgement:
    pass

# not a model! a subclass of this will be dynamically attached to the Notification
# model, based on the Notification's alert_type
class NotificationType(object):
    def __init__(self, notif):
        self._notif = notif

    def __getattr__(self, name):
        if not name.startswith('__'):
            return getattr(self._notif, name)
        else:
            raise AttributeError(name)
