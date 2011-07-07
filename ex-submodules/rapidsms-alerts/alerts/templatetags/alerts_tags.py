from django import template
from logistics.apps.alerts.utils import get_alert_functions
import itertools
from django.template.loader import render_to_string
register = template.Library()

@register.simple_tag
def alerts(request):
    alerts = itertools.chain(*(f(request) for f in get_alert_functions() if f(request) is not None))
    return render_to_string("alerts/partials/alerts.html",
                            {"alerts": alerts})
    
