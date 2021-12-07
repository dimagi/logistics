from logistics_project.apps.malawi.management.commands.deactivate_contacts import DeactivateContactCommand
from rapidsms.models import Contact


class Command(DeactivateContactCommand):
    help = "Deactivates contacts that don't have a connection"
    log_file_name = 'contact-deactivate-fix.txt'

    def get_queryset(self):
        return Contact.objects.filter(connection__id__isnull=True)
