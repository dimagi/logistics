from logistics.models import SupplyPoint
from django.core.management.base import LabelCommand, CommandError
from dimagi.utils.django.management import are_you_sure
import sys


class Command(LabelCommand):
    help = "For a given location, mark it and all it's children as 'pilot'."
    args = "<Location ID>"
    label = "The pk of the Supply Point to mark pilot"

    def handle(self, *args, **options):
        if len(args) != 1: raise CommandError('Please specify %s.' % self.label)

        pk = int(args[0])
        sp = SupplyPoint.objects.get(pk=pk)
        if not are_you_sure("really mark %s as pilot?" % sp):
            print 'ok, canceling'
            sys.exit()
        else:
            mark_pilot(sp)

def mark_pilot(sp):
    print 'marking %s (%s) as pilot' % (sp.name, sp.type)
    # change the name and code from "foo" to "foo-PILOT"
    # deactivate
    _p = lambda s: '%s-PILOT' % s
    sp.name = _p(sp.name)
    sp.code = _p(sp.name)
    sp.active = False
    sp.save()

    # same but for the the location
    if sp.location:
        sp.location.name = _p(sp.location.name)
        sp.location.code = _p(sp.location.code)
        sp.location.is_active = False
        sp.location.save()

    # do the same for all children
    for child in SupplyPoint.objects.filter(supplied_by=sp):
        mark_pilot(child)
