from __future__ import absolute_import

import datetime
import random
import string

from django.contrib.auth.models import User
from django.test import TestCase

from alerts.models import Notification
from logistics.models import SupplyPoint, SupplyPointType
from rapidsms.contrib.locations.models import Location

from logistics_project.apps.ewsghana import notifications


class NotificationTestCase(TestCase):
    "Base test class for creating data need to test notifications."

    def get_random_string(self, length=10):
        "Create a random string."
        return ''.join(random.choice(string.ascii_letters) for x in xrange(length))

    def create_user(self, **kwargs):
        "Create a test user."
        info = {
            'username': self.get_random_string(),
            'password': self.get_random_string(),
            'email': ''
        }
        info.update(kwargs)
        return User.objects.create_user(**info)

    def create_location(self, **kwargs):
        "Create a test location."
        info = {
            'name': self.get_random_string(),
            'code': self.get_random_string(),
        }
        info.update(kwargs)
        return Location.objects.create(**info)

    def create_supply_point_type(self, **kwargs):
        "Create a test supply point type."
        info = {
            'name': self.get_random_string(),
            'code': self.get_random_string(),
        }
        info.update(kwargs)
        return SupplyPointType.objects.create(**info)

    def create_supply_point(self, **kwargs):
        "Create a test supply point."
        info = {
            'name': self.get_random_string(),
            'code': self.get_random_string(),
        }
        info.update(kwargs)
        if 'type' not in info:
            info['type'] = self.create_supply_point_type()
        if 'location' not in info:
            info['location'] = self.create_location()
        return SupplyPoint.objects.create(**info)


class MissingReportNotificationTestCase(NotificationTestCase):
    "Trigger notifications for non-reporting facilities."

    def setUp(self):
        self.facility = self.create_supply_point()
        self.location = self.facility.location
        self.user = self.create_user()
        # Created by post-save handler
        self.profile = self.user.get_profile()
        self.profile.location = self.location
        self.profile.save()

    def test_all_facilities_reported(self):
        "No notifications generated if all have reported."
        self.facility.last_reported = datetime.datetime.now()
        self.facility.save()
        generated = notifications.missing_report_notifications()
        self.assertRaises(StopIteration, generated.next)

    def test_missing_notification(self):
        "Inspect the generated notifcation for a non-reporting facility."
        self.facility.last_reported = datetime.datetime.now() - datetime.timedelta(days=365)
        self.facility.save()
        generated = notifications.missing_report_notifications()
        notification = generated.next()
        self.assertTrue(isinstance(notification._type, notifications.NotReporting))
        self.assertEqual(notification.originating_location, self.location)
        # There should only be one notification
        self.assertRaises(StopIteration, generated.next)
