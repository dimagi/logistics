from django.db import models
from rapidsms.contrib.messagelog.models import Message
from django.contrib.auth.models import User
from datetime import datetime

DEFAULT_MAX_MESSAGES_PER_MONTH = 5

class OutreachQuota(models.Model):
    user = models.OneToOneField(User)
    amount = models.PositiveIntegerField(default=DEFAULT_MAX_MESSAGES_PER_MONTH)

    def __unicode__(self):
        return '{user}: {amt}'.format(user=self.user, amt=self.amount)

    @classmethod
    def get_quota(cls, user):
        quota = cls.objects.get_or_create(user=user)[0]
        return quota.amount

    @classmethod
    def get_remaining(cls, user):
        quota = cls.get_quota(user)
        return quota - OutreachMessage.sent_this_month(user)

class OutreachMessage(models.Model):
    """
    A message that was sent via outreach (directly from the website)
    """
    date = models.DateTimeField(default=datetime.utcnow)
    sent_by = models.ForeignKey(User)
    # sort of duplicate but will be useful for querying 

    def __repr__(self): return str(self)

    def __unicode__(self):
        return 'message on {date} sent by {user}'.format(
            date=self.date,
            user=self.user,
        )

    @classmethod
    def sent_this_month(cls, user):
        today = datetime.utcnow()
        thefirst = datetime(today.year, today.month, 1)
        return cls.objects.filter(sent_by=user,
                                  date__gte=thefirst).count()
