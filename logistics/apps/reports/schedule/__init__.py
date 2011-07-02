""" Utility that turns django views into emailable html reports """

from django.contrib.sites.models import Site
from django.http import HttpRequest
from django.template.loader import render_to_string
from logistics.apps.reports.schedule.parsers import ReportParser
from logistics.apps.reports.schedule.request import RequestProcessor

class ReportSchedule(object):
    """
    A basic report scedule, fully customizable, but requiring you to 
    understand exactly what to pass to the view at runtime.
    """
    def __init__(self, view_func, title="unspecified", 
                 processor=RequestProcessor()):
        self._view_func = view_func
        self._processor = processor
        self._title = title
    
    @property
    def title(self):
        return self._title
    
    def get_response(self, user, view_args={}):
        # these three lines are a complicated way of saying request.user = user.
        # could simplify if the abstraction doesn't make sense.
        request = HttpRequest()
        self._processor.preprocess(request, user=user)
        response = self._view_func(request, **view_args)
        parser = ReportParser(response.content)
        site = Site.objects.get()
        return render_to_string("reports/report_email.html", 
                                { "report_body": parser.get_html(), 
                                  "site": site })
