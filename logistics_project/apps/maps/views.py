from django.template.context import RequestContext
from django.shortcuts import render_to_response
from rapidsms.contrib.locations.models import Location
from django.conf import settings
from logistics.models import SupplyPoint


def dashboard(request):
    # temporary list for now
    # TODO: add type/hierarchical filtering
    supply_points = SupplyPoint.objects.exclude(location__point=None)
    return render_to_response("maps/dashboard.html",
                              {"supply_points": supply_points,
                               "default_latitude":  settings.MAP_DEFAULT_LATITUDE,
                               "default_longitude": settings.MAP_DEFAULT_LONGITUDE,
                               },                             
                              context_instance=RequestContext(request))