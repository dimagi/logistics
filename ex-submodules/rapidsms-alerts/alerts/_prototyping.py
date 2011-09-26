from alerts import Alert
from alerts.models import Notification, NotificationComment, NotificationType

def alerttest(request):
    """
    Example method for adding alerts to your application. This one
    just returns a single empty alert.skype:carterpowers
    """
    return [Alert('intruder alert! intruder alert!', 'http://google.com')]

def notiftest1():
    for i in range(3):
        notif = Notification(alert_type='alerts._prototyping.TestAlertType')
        notif.uid = 'notif-%d' % i
        notif.text = 'This is alert %d' % i
        notif.url = 'http://google.com'
        yield notif

def notiftest2():
    for i in range(2, 5):
        notif = Notification(alert_type='alerts._prototyping.TestAlertType')
        notif.uid = 'notif-%d' % i
        notif.text = 'This is alert %d' % i
        yield notif

class TestAlertType(NotificationType):
    def test(self):
        return '%s %s %s' % (self.text, self.status, str(self.actions(None)))



