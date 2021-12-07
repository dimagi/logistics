from logistics_project.apps.malawi.management.commands.deactivate_contacts import DeactivateContactCommand
from rapidsms.models import Contact


class Command(DeactivateContactCommand):
    help = "Deactivates all active contacts."
    log_file_name = 'contact-deactivate-fix.txt'

    def get_queryset(self):
        return Contact.objects.filter(is_active=True)
