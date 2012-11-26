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
from logistics.util import config
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
        self.district = self.create_location(code=config.LocationCodes.DISTRICT)
        self.facility = self.create_supply_point(location=self.district)
        self.user = self.create_user()
        # Created by post-save handler
        self.profile = self.user.get_profile()
        self.profile.location = self.district
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
        self.assertEqual(notification.owner, self.user)
        # There should only be one notification
        self.assertRaises(StopIteration, generated.next)

    def test_facility_in_district(self):
        "Facility location can be any child of the district."
        location = self.create_location(parent=self.district)
        self.facility.location = location
        self.facility.last_reported = datetime.datetime.now() - datetime.timedelta(days=365)
        self.facility.save()
        generated = notifications.missing_report_notifications()
        notification = generated.next()
        self.assertEqual(notification.owner, self.user)

    def test_multiple_users(self):
        "Each user will get their own notification."
        other_user = self.create_user()
        # Created by post-save handler
        other_profile = other_user.get_profile()
        other_profile.location = self.district
        other_profile.save()
        self.facility.last_reported = datetime.datetime.now() - datetime.timedelta(days=365)
        self.facility.save()
        notified_users = set()
        count = 0
        for notification in notifications.missing_report_notifications():
            notified_users.add(notification.owner)
            count += 1
        self.assertEqual(count, 2)
        self.assertEqual(set([self.user, other_user, ]), notified_users)

    def test_product_type_filter(self):
        "User can recieve missing notifications for only certain product type."
        other_user = self.create_user()
        # Created by post-save handler
        other_profile = other_user.get_profile()
        other_profile.location = self.district
        # This user only cares about another product type
        # should not get a notification
        other_profile.program = self.create_product_type()
        other_profile.save()
        product = self.create_product_stock(supply_point=self.facility)
        other_product = self.create_product_stock(supply_point=self.facility)
        self.facility.last_reported = datetime.datetime.now() - datetime.timedelta(days=365)
        self.facility.save()
        notified_users = set()
        count = 0
        for notification in notifications.missing_report_notifications():
            notified_users.add(notification.owner)
            count += 1
        self.assertEqual(count, 1)
        self.assertEqual(set([self.user, ]), notified_users)

    def test_incomplete_with_filter(self):
        """
        User with product type filter will get notification all products of that
        type are missing reports.
        """
        self.profile.program = self.create_product_type()
        self.profile.save()
        product = self.create_product_stock(supply_point=self.facility)
        product.product.type = self.profile.program
        product.product.save()
        stock_on_hand = self.create_product_report_type(code=Reports.SOH)
        self.create_product_report(
            supply_point=self.facility, product=product.product,
            report_type=stock_on_hand, report_date=datetime.datetime.now() - datetime.timedelta(days=365)
        )
        other_product = self.create_product_stock(supply_point=self.facility)
        other_product.product.type = self.profile.program
        other_product.product.save()
        notified_users = set()
        count = 0
        for notification in notifications.missing_report_notifications():
            notified_users.add(notification.owner)
            count += 1
        self.assertEqual(count, 1)
        self.assertEqual(set([self.user, ]), notified_users)


class IncompleteReportNotificationTestCase(NotificationTestCase):
    "Trigger notifications for facilities with incomplete reports."

    def setUp(self):
        self.district = self.create_location(code=config.LocationCodes.DISTRICT)
        self.facility = self.create_supply_point(location=self.district)
        self.user = self.create_user()
        # Created by post-save handler
        self.profile = self.user.get_profile()
        self.profile.location = self.district
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
        self.assertEqual(notification.owner, self.user)
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
        self.assertEqual(notification.owner, self.user)
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

    def test_facility_in_district(self):
        "Facility location can be any child of the district."
        location = self.create_location(parent=self.district)
        self.facility.location = location
        self.facility.save()
        product = self.create_product_stock(supply_point=self.facility)
        product_report = self.create_product_report(
            supply_point=self.facility, product=product.product,
            report_type=self.stock_on_hand
        )
        other_product = self.create_product_stock(supply_point=self.facility)
        generated = notifications.incomplete_report_notifications()
        notification = generated.next()
        self.assertEqual(notification.owner, self.user)

    def test_multiple_users(self):
        "Each user will get their own notification."
        other_user = self.create_user()
        # Created by post-save handler
        other_profile = other_user.get_profile()
        other_profile.location = self.district
        other_profile.save()
        product = self.create_product_stock(supply_point=self.facility)
        product_report = self.create_product_report(
            supply_point=self.facility, product=product.product,
            report_type=self.stock_on_hand
        )
        other_product = self.create_product_stock(supply_point=self.facility)
        notified_users = set()
        count = 0
        for notification in notifications.incomplete_report_notifications():
            notified_users.add(notification.owner)
            count += 1
        self.assertEqual(count, 2)
        self.assertEqual(set([self.user, other_user, ]), notified_users)

    def test_product_type_filter(self):
        "User can recieve notifications for only certain product type."
        other_user = self.create_user()
        # Created by post-save handler
        other_profile = other_user.get_profile()
        other_profile.location = self.district
        # This user only cares about another product type
        # should not get a notification
        other_profile.program = self.create_product_type()
        other_profile.save()
        product = self.create_product_stock(supply_point=self.facility)
        self.create_product_report(
            supply_point=self.facility, product=product.product,
            report_type=self.stock_on_hand
        )
        other_product = self.create_product_stock(supply_point=self.facility)
        notified_users = set()
        count = 0
        for notification in notifications.incomplete_report_notifications():
            notified_users.add(notification.owner)
            count += 1
        self.assertEqual(count, 1)
        self.assertEqual(set([self.user, ]), notified_users)

    def test_incomplete_with_filter(self):
        """
        User with product type filter will get notification if only some of
        products of that type are reported.
        """
        self.profile.program = self.create_product_type()
        self.profile.save()
        product = self.create_product_stock(supply_point=self.facility)
        product.product.type = self.profile.program
        product.product.save()
        product_report = self.create_product_report(
            supply_point=self.facility, product=product.product,
            report_type=self.stock_on_hand
        )
        other_product = self.create_product_stock(supply_point=self.facility)
        other_product.product.type = self.profile.program
        other_product.product.save()
        generated = notifications.incomplete_report_notifications()
        notification = generated.next()
        self.assertTrue(isinstance(notification._type, notifications.IncompelteReporting))
        self.assertEqual(notification.owner, self.user)


class StockoutReportNotificationTestCase(NotificationTestCase):
    "Trigger notifications for facilities with stockouts."

    def setUp(self):
        self.district = self.create_location(code=config.LocationCodes.DISTRICT)
        self.facility = self.create_supply_point(location=self.district)
        self.user = self.create_user()
        # Created by post-save handler
        self.profile = self.user.get_profile()
        self.profile.location = self.district
        self.profile.save()
        self.stock_on_hand = self.create_product_report_type(code=Reports.SOH)

    def test_missing_notification(self):
        "No notification if there were no reports. Covered by missing report."
        generated = notifications.stockout_notifications()
        self.assertRaises(StopIteration, generated.next)

    def test_all_products_stocked(self):
        "No notification if all products are stocked."
        product = self.create_product_stock(supply_point=self.facility)
        self.create_product_report(
            supply_point=self.facility, product=product.product,
            report_type=self.stock_on_hand, quantity=10
        )
        generated = notifications.stockout_notifications()
        self.assertRaises(StopIteration, generated.next)

    def test_simple_stockout(self):
        "Single product, single report with 0 quantity."
        product = self.create_product_stock(supply_point=self.facility)
        self.create_product_report(
            supply_point=self.facility, product=product.product,
            report_type=self.stock_on_hand, quantity=0
        )
        generated = notifications.stockout_notifications()
        notification = generated.next()
        self.assertTrue(isinstance(notification._type, notifications.Stockout))
        self.assertEqual(notification.owner, self.user)
        # There should only be one notification
        self.assertRaises(StopIteration, generated.next)

    def test_multi_report_stockout(self):
        "Single product, mutliple reports with 0 quantity."
        product = self.create_product_stock(supply_point=self.facility)
        self.create_product_report(
            supply_point=self.facility, product=product.product,
            report_type=self.stock_on_hand, quantity=0
        )
        self.create_product_report(
            supply_point=self.facility, product=product.product,
            report_type=self.stock_on_hand, quantity=0
        )
        self.create_product_report(
            supply_point=self.facility, product=product.product,
            report_type=self.stock_on_hand, quantity=0
        )
        generated = notifications.stockout_notifications()
        notification = generated.next()
        self.assertTrue(isinstance(notification._type, notifications.Stockout))
        self.assertEqual(notification.owner, self.user)
        # There should only be one notification
        self.assertRaises(StopIteration, generated.next)

    def test_partial_duration_stockout(self):
        "Some reports indicate a stockout but did not last the entire period. No notification."
        product = self.create_product_stock(supply_point=self.facility)
        self.create_product_report(
            supply_point=self.facility, product=product.product,
            report_type=self.stock_on_hand, quantity=0
        )
        self.create_product_report(
            supply_point=self.facility, product=product.product,
            report_type=self.stock_on_hand, quantity=1
        )
        generated = notifications.stockout_notifications()
        self.assertRaises(StopIteration, generated.next)

    def test_partial_product_stockout(self):
        "Multiple products but only one is stocked out. Should be reported."
        product = self.create_product_stock(supply_point=self.facility)
        self.create_product_report(
            supply_point=self.facility, product=product.product,
            report_type=self.stock_on_hand, quantity=0
        )
        other_product = self.create_product_stock(supply_point=self.facility)
        self.create_product_report(
            supply_point=self.facility, product=other_product.product,
            report_type=self.stock_on_hand, quantity=10
        )
        generated = notifications.stockout_notifications()
        notification = generated.next()
        self.assertEqual(notification.owner, self.user)
        # There should only be one notification
        self.assertRaises(StopIteration, generated.next)

    def test_facility_in_district(self):
        "Facility location can be any child of the district."
        location = self.create_location(parent=self.district)
        self.facility.location = location
        self.facility.save()
        product = self.create_product_stock(supply_point=self.facility)
        self.create_product_report(
            supply_point=self.facility, product=product.product,
            report_type=self.stock_on_hand, quantity=0
        )
        generated = notifications.stockout_notifications()
        notification = generated.next()
        self.assertTrue(isinstance(notification._type, notifications.Stockout))
        self.assertEqual(notification.owner, self.user)

    def test_multiple_users(self):
        "Each user will get their own notification."
        other_user = self.create_user()
        # Created by post-save handler
        other_profile = other_user.get_profile()
        other_profile.location = self.district
        other_profile.save()
        product = self.create_product_stock(supply_point=self.facility)
        self.create_product_report(
            supply_point=self.facility, product=product.product,
            report_type=self.stock_on_hand, quantity=0
        )
        notified_users = set()
        count = 0
        for notification in notifications.stockout_notifications():
            notified_users.add(notification.owner)
            count += 1
        self.assertEqual(count, 2)
        self.assertEqual(set([self.user, other_user, ]), notified_users)

    def test_product_type_filter(self):
        "User can recieve notifications for only certain product type."
        other_user = self.create_user()
        # Created by post-save handler
        other_profile = other_user.get_profile()
        other_profile.location = self.district
        # This user only cares about another product type
        # should not get a notification
        other_profile.program = self.create_product_type()
        other_profile.save()
        product = self.create_product_stock(supply_point=self.facility)
        self.create_product_report(
            supply_point=self.facility, product=product.product,
            report_type=self.stock_on_hand, quantity=0
        )
        notified_users = set()
        count = 0
        for notification in notifications.stockout_notifications():
            notified_users.add(notification.owner)
            count += 1
        self.assertEqual(count, 1)
        self.assertEqual(set([self.user, ]), notified_users)


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
        self.notification = self.create_notification(owner=self.user)

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
