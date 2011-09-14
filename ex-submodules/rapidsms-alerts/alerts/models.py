from django.db import models
from django.contrib.auth.models import User

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

    # link to an AlertType?
    owner = models.ForeignKey(User, null=True, blank=True)
    status = models.CharField(max_length=10, choices=NOTIF_STATUS, default='new')

    def __unicode__(self):
        return unicode(self.__dict__)

class NotificationComment(models.Model):
    notification = models.ForeignKey(Notification, related_name='comments')
    user = models.ForeignKey(User, null=True, blank=True) #no user is for system-generated entries
    date = models.DateTimeField(auto_now_add=True)
    text = models.TextField()
