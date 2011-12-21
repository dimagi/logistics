from alerts import Alert
from alerts.models import Notification, NotificationComment, NotificationType
from django.contrib.auth.models import User
from rapidsms.contrib.locations.models import Location
from rapidsms.models import Contact
from datetime import datetime, timedelta
from cvs.utils import total_attribute_value

def alerttest(request):
    """
    Example method for adding alerts to your application. This one
    just returns a single empty alert.
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
            return [User.objects.get(username='droos')]
        elif esc_level == 'moh':
            #all users with group 'moh'
            return [User.objects.get(username='admin')]

    def auto_escalation_interval(self, esc_level):
        return timedelta(minutes=2) #days=14)

    def escalation_level_name(self, esc_level):
        return {
            'district': 'district team',
            'moh': 'ministry of health',
            }[esc_level]

def mk_notifiable_disease_alert(disease, alert_type, reporting_period, val, loc):
    notif = Notification(alert_type=alert_type)
    notif.uid = 'disease_%s_%s_%s' % (disease, reporting_period, loc.code)
    notif.text = '%d cases of %s reported in %s %s' % (val, disease, loc.name, loc.type.name)
    notif.url = None
    notif.originating_location = loc
    return notif

def notifiable_disease_test():
    METRICS = {
        'malaria': {
            'threshold': 3,
            'slug': 'epi_ma',
            'gen': mk_notifiable_disease_alert,
        }
    }
    REPORTING_INTERVAL = 'weekly'

    timestamp = datetime.now()
    if REPORTING_INTERVAL == 'weekly':
        yr, wk, dow = timestamp.isocalendar()
        reporting_period = '%dw%02d' % (yr, wk)
        period_start = timestamp.date() - timedelta(days=dow-1)
        period_end = period_start + timedelta(days=6)
    else:
        raise Exception('unsupported reporting interval [%s]' % REPORTING_INTERVAL)

    for metric, info in METRICS.iteritems():
        #todo: is the end date inclusive or exclusive?
        data = total_attribute_value(info['slug'], period_start, period_end, Location.objects.get(name='Uganda'))
        for total in data:
            loc = Location.objects.get(id=total['location_id'])
            val = total['value']

            if val > info['threshold']:
                # trigger alert
                yield info['gen'](metric, 'alerts._prototyping.NotifiableDiseaseThresholdAlert', reporting_period, val, loc)

# this should serve as the template for most front-line alerts
class NotifiableDiseaseThresholdAlert(NotificationType):
    escalation_levels = ['district', 'moh']

    def users_for_escalation_level(self, esc_level):
        if esc_level == 'district':
            #all users with reporting_district = district
            return [c.user for c in Contact.objects.filter(reporting_location=self.originating_location) if c.user]
        elif esc_level == 'moh':
            #all users with group 'moh'
            return [User.objects.get(username='admin')] #todo: is there an moh 'group'?

    def auto_escalation_interval(self, esc_level):
        return timedelta(minutes=5) #days=14)

    def escalation_level_name(self, esc_level):
        return {
            'district': 'district team',
            'moh': 'ministry of health',
            }[esc_level]


