import unittest
from rapidsms.tests.scripted import TestScript
from rapidsms.contrib.messagelog.models import Message
from taggit.models import Tag

class TestTags(TestScript):

    def testMessageTagging(self):

        self.assertInteraction("""                                                                                              8005551212 > register as someuser                                                                                     8005551212 < Thank you for registering, as someuser!                                                                """)
        
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

