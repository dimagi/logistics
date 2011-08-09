from logistics.decorators import place_in_request
from logistics.models import SupplyPoint
from logistics.views import get_facilities
from logistics.reports import ReportingBreakdown
from dimagi.utils.dates import DateSpan
from datetime import datetime
from django.shortcuts import render_to_response
from django.template.context import RequestContext


@place_in_request()
def dashboard(request):
    
    base_facilities = SupplyPoint.objects.filter(active=True, type__code="hsa")
    em_group = None
    begin_date = None
    # district filter
    if request.location:
        valid_facilities = get_facilities().filter(parent_id=request.location.pk)
        base_facilities = base_facilities.filter(location__parent_id__in=[f.pk for f in valid_facilities])
        #em_group = (group_for_location(request.location) == config.Groups.EM)
    # reporting info
    report = ReportingBreakdown(base_facilities, DateSpan.since(30))#(group == config.Groups.EM))
    if em_group:
        begin_date = datetime.now().replace(day=1)
        end_date = datetime.now()
        d = DateSpan(begin_date, end_date)
        em_report = ReportingBreakdown(base_facilities, d, include_late = True, MNE=False)#(group == config.Groups.EM))
    else:
        em_report = None
    return render_to_response("tanzania/dashboard.html",
                              {"reporting_data": report,
#                               "hsas_table": MalawiContactTable(Contact.objects.filter(is_active=True,
#                                                                                       role__code="hsa"), request=request),
                               "graph_width": 200,
                               "graph_height": 200,
                               "em_group": em_group,
                               "em_report": em_report,
                               "begin_date": begin_date,
                               #"districts": get_districts().order_by("code"),
                               "location": request.location},
                               
                              context_instance=RequestContext(request))

