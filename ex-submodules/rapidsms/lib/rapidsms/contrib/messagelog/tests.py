from __future__ import unicode_literals

from logistics_project.apps.malawi.tests import create_hsa, MalawiTestBase
from rapidsms.tests.scripted import TestScript
from rapidsms.contrib.messagelog.models import Message
from taggit.models import Tag


class TestTags(TestScript):

    def testMessageTagging(self):

        self.assertInteraction("""
            +8005551212 > register as someuser
            +8005551212 < Sorry, I didn't understand. To register, send register [first name] [last name] [id] [facility]. Example: 'register john smith 1 1001'
        """)
        
        self.assertEqual(0, len(Message.objects.all()[0].tags.all()))
        
        m = Message.objects.all()[0]
        m.tags.add('test')
        m.save()
        
        self.assertEqual(1, len(Message.objects.all()[0].tags.all()))
        self.assertEqual(1, len(Message.objects.filter(tags__name__in=['test'])))
        self.assertEqual(1, len(Tag.objects.all()))
        
        m = Message.objects.get(pk=m.pk)
        m.tags.add('test2')
        m.save()

        self.assertEqual(2, len(Message.objects.all()[0].tags.all()))
        self.assertEqual(1, len(Message.objects.filter(tags__name__in=['test2'])))
        self.assertEqual(2, len(Tag.objects.all()))

        m = Message.objects.exclude(pk=m.pk)[0]
        m.tags.add('test')
        m.save()

        self.assertEqual(1, len(Message.objects.all()[1].tags.all()))
        self.assertEqual(2, len(Message.objects.filter(tags__name__in=['test'])))
        self.assertEqual(2, len(Tag.objects.all()))


class TestContactLastMessage(MalawiTestBase):

    def test_last_message(self):
        contact = create_hsa(self, '+5558585', 'Logger Head')
        # ideally this wouldn't be None, but it is because the message is logged before the contact is created
        self.assertEqual(None, contact.last_message)
        self.runScript("""
            +5558585 > help
        """)
        contact.refresh_from_db()
        self.assertEqual('help', contact.last_message.text)
        self.runScript("""
            +5558585 > help again
        """)
        contact.refresh_from_db()
        self.assertEqual('help again', contact.last_message.text)
