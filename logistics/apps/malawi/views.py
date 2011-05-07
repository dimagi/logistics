from django.shortcuts import render_to_response
from django.template.context import RequestContext


def dashboard(request):
    return render_to_response("malawi/dashboard.html", {}, 
                              context_instance=RequestContext(request))
    