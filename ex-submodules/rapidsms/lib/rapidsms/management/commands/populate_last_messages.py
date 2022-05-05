from django.core.management.base import BaseCommand

from rapidsms.models import Contact


class Command(BaseCommand):
    help = "Populate last message objects on all contacts."

    def handle(self, **options):
        contacts = Contact.objects.filter(is_active=True, last_message=None)
        contact_count = contacts.count()
        for i, contact in enumerate(contacts):
            print(f'processing contact {i}/{contact_count}...')
            if contact.message_set.filter(direction='I').exists():
                last_message = contact.message_set.filter(direction='I').order_by('-date')[0]
                contact.last_message = last_message
                contact.save()
