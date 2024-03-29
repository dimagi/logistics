from __future__ import print_function
from __future__ import unicode_literals
from django.core.management.base import BaseCommand
from rapidsms.models import App
from ...conf import settings


class Command(BaseCommand):
    help = "Creates instances of the App model stub for all running apps."


    def handle(self, **options):
        verbosity = int(options.get("verbosity", 1))
        
        # fetch all of the apps (identified by their module name,
        # which is unique) that we already have objects for
        known_module_names = list(App.objects\
            .values_list("module", flat=True))

        # find any running apps which currently
        # don't have objects, and fill in the gaps
        for module_name in settings.INSTALLED_APPS:
            if not module_name in known_module_names:
                known_module_names.append(module_name)
                app = App.objects.create(
                    module=module_name)

                # log at the same level as syncdb's "created table..."
                # messages, to stay silent when called with -v 0
                if verbosity >= 1:
                    print("Added persistant app %s" % app)
