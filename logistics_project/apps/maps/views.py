from django.template.context import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from rapidsms.contrib.locations.models import Location
from django.conf import settings
from logistics.models import SupplyPoint
from logistics.decorators import place_in_request


@place_in_request()
def dashboard(request, location_code=None):
    # temporary list for now
    # TODO: add type/hierarchical filtering
    # whole country
    location = request.location if request.location else get_object_or_404(Location, code=settings.COUNTRY)
    supply_points = location.all_facilities().exclude(location__point=None)
    return render_to_response("maps/dashboard.html",
                              {"supply_points": supply_points,
                               "default_latitude":  settings.MAP_DEFAULT_LATITUDE,
                               "default_longitude": settings.MAP_DEFAULT_LONGITUDE,
                               "location": location,
                               "destination_url": "maps_dashboard",
                               },                             
                              context_instance=RequestContext(request))