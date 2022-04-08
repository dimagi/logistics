from __future__ import unicode_literals
from django.conf import settings

from rapidsms.models import Contact, Connection, Backend
from rapidsms.tests.scripted import TestScript

class TestContact(TestScript):
    def setUp(self):
        Connection.objects.all().delete()
        Contact.objects.all().delete()
        Backend.objects.create(name=settings.DEFAULT_BACKEND)
        
    def tearDown(self):
        Connection.objects.all().delete()
        Contact.objects.all().delete()
        Backend.objects.get(name=settings.DEFAULT_BACKEND).delete()
      
    def test_set_default_connection_nodefaultbefore_newconnection(self):
        # create new connection
        contact = Contact.objects.create()
        contact.default_connection = '123'
        contact.save()
        conn = Connection.objects.get()
        self.assertEqual(conn.contact, contact)
        self.assertEqual(conn.identity, '123')
    
    def test_set_default_connection_nodefaultbefore_existingconnection(self):
        # assign connection to this user
        contact = Contact.objects.create()
        contact.default_connection = '123'
        contact2 = Contact.objects.create()
        contact2.default_connection = '123'
        conn = Connection.objects.get()
        self.assertEqual(conn.contact, contact2)
        self.assertEqual(conn.identity, '123')
        self.assertEqual(contact.default_connection, None)
    
    def test_set_default_connection_defaultbefore_existingconnection(self):
        contact = Contact.objects.create()
        contact.default_connection = '456'
        contact2 = Contact.objects.create()
        contact2.default_connection = '123'
        contact.default_connection = '123'
        conn = Connection.objects.get(identity='123')
        self.assertEqual(conn.contact, contact)
        self.assertEqual(conn.identity, '123')
        self.assertEqual(contact2.default_connection, None)
