from __future__ import absolute_import

import datetime
import random
import string

from django.contrib.auth.models import User
from django.test import TestCase

from alerts.models import Notification, NotificationVisibility
from logistics.const import Reports
from logistics.models import SupplyPoint, SupplyPointType, ProductType, Product
from logistics.models import ProductStock, ProductReportType, ProductReport
from mock import patch
from rapidsms.contrib.locations.models import Location
from rapidsms.models import Connection, Contact, Backend

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

    def create_product_type(self, **kwargs):
        "Create a test product type."
        info = {
            'name': self.get_random_string(),
            'code': self.get_random_string(),
        }
        info.update(kwargs)
        return ProductType.objects.create(**info)

    def create_product(self, **kwargs):
        "Create a test product."
        info = {
            'name': self.get_random_string(),
            'units': self.get_random_string(),
            'sms_code': self.get_random_string(),
            'description': self.get_random_string(),
        }
        info.update(kwargs)
        if 'type' not in info:
            info['type'] = self.create_product_type()
        return Product.objects.create(**info)

    def create_product_stock(self, **kwargs):
        "Associate a test product with facility."
        info = {}
        info.update(kwargs)
        if 'product' not in info:
            info['product'] = self.create_product()
        if 'supply_point' not in info:
            info['supply_point'] = self.create_supply_point()
        return ProductStock.objects.create(**info)

    def create_product_report_type(self, **kwargs):
        "Create a test product report type."
        info = {
            'name': self.get_random_string(),
            'code': self.get_random_string(),
        }
        info.update(kwargs)
        return ProductReportType.objects.create(**info)

    def create_product_report(self, **kwargs):
        "Fake stock report submission."
        info = {
            'quantity': random.randint(1, 25)
        }
        info.update(kwargs)
        if 'product' not in info:
            info['product'] = self.create_product()
        if 'supply_point' not in info:
            info['supply_point'] = self.create_supply_point()
        if 'report_type' not in info:
            info['report_type'] = self.create_product_report_type()
        return ProductReport.objects.create(**info)

    def create_backend(self, **kwargs):
        "Create test backend."
        info = {
            'name': self.get_random_string(),
        }
        info.update(kwargs)
        return Backend.objects.create(**info)

    def create_contact(self, **kwargs):
        "Create test contact."
        info = {
            'name': self.get_random_string(),
        }
        info.update(kwargs)
        return Contact.objects.create(**info)

    def create_connection(self, **kwargs):
        info = {
            'identity': self.get_random_string(),
        }
        info.update(kwargs)
        if 'backend' not in info:
            info['backend'] = self.create_backend()
        return Connection.objects.create(**info)

    def create_notification(self, **kwargs):
        "Create a test notification."
        alert_class = random.choice([
            notifications.NotReporting,
            notifications.IncompelteReporting,
            notifications.Stockout,
        ])
        alert_type = alert_class.__module__ + '.' + alert_class.__name__
        info = {
            'uid': self.get_random_string(),
            'text': self.get_random_string(),
            'alert_type': alert_type,
            'escalation_level': '',
            'escalated_on': datetime.datetime.now(),
        }
        info.update(kwargs)
        return Notification.objects.create(**info)


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


class IncompleteReportNotificationTestCase(NotificationTestCase):
    "Trigger notifications for facilities with incomplete reports."

    def setUp(self):
        self.facility = self.create_supply_point()
        self.location = self.facility.location
        self.user = self.create_user()
        # Created by post-save handler
        self.profile = self.user.get_profile()
        self.profile.location = self.location
        self.profile.save()
        self.stock_on_hand = self.create_product_report_type(code=Reports.SOH)

    def test_missing_notification(self):
        "No notification if there were no reports. Covered by missing report."
        generated = notifications.incomplete_report_notifications()
        self.assertRaises(StopIteration, generated.next)

    def test_all_products_reported(self):
        "No notification if all products were reported."
        product = self.create_product_stock(supply_point=self.facility)
        product_report = self.create_product_report(
            supply_point=self.facility, product=product.product,
            report_type=self.stock_on_hand
        )
        other_product = self.create_product_stock(supply_point=self.facility)
        other_report = self.create_product_report(
            supply_point=self.facility, product=other_product.product,
            report_type=self.stock_on_hand
        )
        generated = notifications.incomplete_report_notifications()
        self.assertRaises(StopIteration, generated.next)

    def test_missing_product(self):
        "One product has no reports."
        product = self.create_product_stock(supply_point=self.facility)
        product_report = self.create_product_report(
            supply_point=self.facility, product=product.product,
            report_type=self.stock_on_hand
        )
        other_product = self.create_product_stock(supply_point=self.facility)
        generated = notifications.incomplete_report_notifications()
        notification = generated.next()
        self.assertTrue(isinstance(notification._type, notifications.IncompelteReporting))
        self.assertEqual(notification.originating_location, self.location)
        # There should only be one notification
        self.assertRaises(StopIteration, generated.next)

    def test_old_product_report(self):
        "One product has an old report."
        product = self.create_product_stock(supply_point=self.facility)
        product_report = self.create_product_report(
            supply_point=self.facility, product=product.product,
            report_type=self.stock_on_hand
        )
        other_product = self.create_product_stock(supply_point=self.facility)
        other_report = self.create_product_report(
            supply_point=self.facility, product=other_product.product,
            report_type=self.stock_on_hand,
            report_date=datetime.datetime.now() - datetime.timedelta(days=365)
        )
        generated = notifications.incomplete_report_notifications()
        notification = generated.next()
        self.assertTrue(isinstance(notification._type, notifications.IncompelteReporting))
        self.assertEqual(notification.originating_location, self.location)
        # There should only be one notification
        self.assertRaises(StopIteration, generated.next)

    def test_inactive_product(self):
        "Don't trigger notifications for missing products if they are not active."
        product = self.create_product_stock(supply_point=self.facility)
        product_report = self.create_product_report(
            supply_point=self.facility, product=product.product,
            report_type=self.stock_on_hand
        )
        other_product = self.create_product_stock(supply_point=self.facility, is_active=False)
        generated = notifications.incomplete_report_notifications()
        self.assertRaises(StopIteration, generated.next)


class SMSNotificationTestCase(NotificationTestCase):
    "Saved notifications should trigger SMS to users with associated contacts."

    def setUp(self):
        self.facility = self.create_supply_point()
        self.location = self.facility.location
        self.user = self.create_user()
        # Created by post-save handler
        self.profile = self.user.get_profile()
        self.profile.location = self.location
        self.profile.contact = self.create_contact()
        self.profile.save()
        self.connection = self.create_connection(contact=self.profile.contact)
        self.notification = self.create_notification(originating_location=self.location)

    def test_send_sms(self):
        "Successful SMS sent."
        with patch('logistics_project.apps.ewsghana.notifications.send_message') as send:
            # Sets initial escalation level and reveals to users
            self.notification.initialize()
            self.assertTrue(send.called)
            args, kwargs = send.call_args
            connection, text = args
            self.assertEqual(connection, self.connection)
            self.assertEqual(text, self.notification.text)

    def test_no_contact(self):
        "No message will be sent if user doesn't have an associated contact."
        self.profile.contact = None
        self.profile.save()
        with patch('logistics_project.apps.ewsghana.notifications.send_message') as send:
            # Sets initial escalation level and reveals to users
            self.notification.initialize()
            self.assertFalse(send.called)

    def test_no_connections(self):
        "No message will be sent if contact doesn't have an associated connection."
        self.connection.delete()
        with patch('logistics_project.apps.ewsghana.notifications.send_message') as send:
            # Sets initial escalation level and reveals to users
            self.notification.initialize()
            self.assertFalse(send.called)

    def test_different_location(self):
        "User will not get SMS if they are in another location."
        self.profile.location = self.create_location()
        self.profile.save()
        with patch('logistics_project.apps.ewsghana.notifications.send_message') as send:
            # Sets initial escalation level and reveals to users
            self.notification.initialize()
            self.assertFalse(send.called)

    def test_multiple_recipients(self):
        "Each user will get their own SMS."
        other_user = self.create_user()
        # Created by post-save handler
        other_profile = other_user.get_profile()
        other_profile.location = self.location
        other_profile.contact = self.create_contact()
        other_profile.save()
        other_connection = self.create_connection(contact=other_profile.contact)
        with patch('logistics_project.apps.ewsghana.notifications.send_message') as send:
            # Sets initial escalation level and reveals to users
            self.notification.initialize()
            self.assertEqual(send.call_count, 2)

