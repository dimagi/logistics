from alerts import Alert
from alerts.models import Notification, NotificationComment, NotificationType
from datetime import timedelta

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
    escalation_levels = ['district', 'moh']

    def users_for_escalation_level(self, esc_level):
        if esc_level == 'district':
            #all users with reporting_district = district
            return []
        elif esc_level == 'moh':
            #all users with group 'moh'
            return []

    def auto_escalation_interval(self, esc_level):
        return timedelta(days=14)

    def escalation_level_name(self, esc_level):
        return {
            'district': 'district team',
            'moh': 'ministry of health',
            }[esc_level]



