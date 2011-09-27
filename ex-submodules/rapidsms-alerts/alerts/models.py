from django.db import models
from django.contrib.auth.models import User
from rapidsms.contrib.locations.models import Location
from django.conf import settings
from django.utils.dateformat import format as format_date
from alerts.importutil import dynamic_import
from datetime import datetime

class Notification(models.Model):
    uid = models.CharField(max_length=256)
    created_on = models.DateTimeField(auto_now_add=True)
    escalated_on = models.DateTimeField()

    text = models.TextField()
    url = models.TextField(null=True, blank=True)
    alert_type = models.CharField(max_length=256) #fully-qualified python name of the corresponding AlertType class
    originating_location = models.ForeignKey(Location, blank=True, null=True)

    owner = models.ForeignKey(User, null=True, blank=True)
    is_open = models.BooleanField(default=True)
    escalation_level = models.CharField(max_length=100)

    _type_inst = None #instantiation of the alert_type class; automatically set on demand

    def json(self, user=None):
        return {
            'id': self.id,
            'msg': self.text,
            'url': self.url,
            'owner': user_name(self.owner),
            'status': self.status,
            'comments': [cmt.json() for cmt in self.comments.all()],
            'actions': self.actions(user),
            'esc_class': self.escalation_level_name(self.escalation_level),
        }

    @property
    def is_escalated(self):
        return self.escalation_level != self.initial_escalation_level

    @property
    def status(self):
        if not self.is_open:
            return 'closed'
        elif self.is_escalated:
            return 'esc'
        elif self.owner is None:
            return 'new'
        else:
            return 'fu'

    def actions(self, user):
        """return the actions this user may currently take on this alert"""
        if not self.is_open:
            return []
        else:
            user_esc_level = self.user_escalation_level(user)
            user_level_active = (user_esc_level == self.escalation_level)

            acts = []
            if user_level_active and self.owner != user:
                acts.append('fu')
            if user_level_active and self.is_escalable:
                acts.append('esc')
            acts.append('resolve')
            return acts

    def initialize(self):
        self.set_esc_level(self.initial_escalation_level)

    def resolve(self):
        self.is_open = False

    def followup(self, user):
        self.owner = user

    def escalate(self):
        if not self.is_escalable:
            raise Exception('alert cannot be escalated further')

        self.owner = None
        self.set_esc_level(self.next_escalation_level(self.escalation_level))

    def reveal_to_users(self):
        if self.id is None:
            self.save()

        for u in self.users_for_escalation_level(self.escalation_level):
            nv = NotificationVisibility(notif=self, user=u, esc_level=self.escalation_level)
            nv.save()

    def autoescalate_due(self):
        return (self.is_escalable and datetime.utcnow() - self.escalated_on > self.auto_escalation_interval(self.escalation_level))

    def set_esc_level(self, esc_level):
        self.escalation_level = esc_level
        self.escalated_on = datetime.utcnow()
        self.reveal_to_users()

    def user_escalation_level(self, user):
        """determine at what escalation level this user is affiliated with the
        alert (determines what actions that user may take"""
        vis = self.visible_to.filter(user=user)
        if len(vis) == 0:
            raise Exception('alert is not visible to user')
        elif len(vis) > 1:
            # somehow the same user is registered to handle the alert at multiple
            # escalation levels. this shouldn't happen, but we'll just pick a level
            # TODO: log this
            v = list(vis)[-1]
        else:
            v = vis[0]

        return v.esc_level

    def __unicode__(self):
        return unicode(self.__dict__)

    @property
    def _type(self):
        if not self._type_inst:
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
            'is_system': self.is_system,
        }

    @property
    def is_system(self):
        return self.user is None

    def __unicode__(self):
        return unicode(self.__dict__)

def user_name(user, default=None):
    if user is None:
        return default
    else:
        fname = user.first_name
        lname = user.last_name
        return '%s %s' % (fname, lname) if fname and lname else user.username

# static list of which users can see what alerts. static so that it's fast to query.
# however, if users are added to/removed from the underlying user classes that should
# see the alert, those changes won't be reflected here. perhaps we should keep them
# in sync from a scheduled task -- possibly the same one that does the auto-escalation
# definitely not a priority right now
class NotificationVisibility(models.Model):
    """many-to-many mapping of which users can see which alerts"""
    notif = models.ForeignKey(Notification, related_name='visible_to')
    user = models.ForeignKey(User, related_name='alerts_visible')
    esc_level = models.CharField(max_length=100)

class ResolutionAcknowledgement:
    pass

# not a model! a subclass of this will be dynamically attached to the Notification
# model, based on the Notification's alert_type
class NotificationType(object):
    def __init__(self, notif):
        self._notif = notif

    def __getattr__(self, name):
        #it's important that '__*__' lookups are trapped here. otherwise the
        #introspection in Notification.__getattribute__ will cause an infinite
        #loop
        if not name.startswith('__'):
            return getattr(self._notif, name)
        else:
            raise AttributeError(name)

    @property
    def initial_escalation_level(self):
        return self.next_escalation_level(None)

    @property
    def is_escalable(self):
        return self.next_escalation_level(self.escalation_level) is not None

    def next_escalation_level(self, esc_level):
        """return the escalation level that follows esc_level
        if esc_level is None, return the default (un-escalated) level
        if alert cannot be escalated further, return None"""
        levels = self.escalation_levels
        if esc_level == None:
            return levels[0]
        else:
            try:
                return levels[levels.index(esc_level)+1]
            except IndexError:
                return None

    @property
    def escalation_levels(self):
        """list the possible escalation levels for this type of alert,
        in order"""
        raise Exception('abstract method')

    def users_for_escalation_level(self, esc_level):
        """return the set of users responsible for this alert once it
        reaches the specified escalation level"""
        raise Exception('abstract method')

    def auto_escalation_interval(self, esc_level):
        """return the time interval (as a timedelta) the alert has spent
        at the given level after which it is auto-escalated to the next
        level"""
        raise Exception('abstract method')
        
    def escalation_level_name(self, esc_level):
        """human readable name for the given escalation level (i.e.,
        'district team', 'MoH', 'regional supervisor'"""
        raise Exception('abstract method')
        
