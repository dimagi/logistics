from django.conf import settings
from django.shortcuts import render_to_response
from django.template.context import RequestContext


class WarehouseView(object):
    """
    View class to be extended for each report page 
        with its own custom_context method
    
    Include in settings:

        REPORT_LIST = SortedDict([
        ("Dashboard", "dashboard"),])
    """
    _context = None
    
    def __init__(self, slug):
        self.slug = slug
        self._context = None
    
        
    @property
    def template_name(self):
        """
        The template that should be used for this.
        """
        # should be overridden
        return "%s.html" % self.slug
     
    def can_view(self, request):
        """
        Whether this report can be viewed - typically based of the user and 
        potentially other information in the request.
        """
        # should be overridden if you want to restrict things
        return True
    
    def get_response(self, request):
        """
        The HTTP Response object for this report
        """
        return render_to_response(self.template_name, 
                                  self.get_context(request),
                                  context_instance=RequestContext(request))

    
    def shared_context(self, request):
        """
        Add this to your subclasses shared_context method:

        base_context = super(<YourWarehouseViewSubclass>, self).shared_context(request)
        """
        to_stub = lambda x: {"name": x, "slug": settings.REPORT_LIST[x]}
        stub_reports = [to_stub(r) for r in settings.REPORT_LIST.keys()]

        return { 
            "report_list": stub_reports,
            "settings": settings
        }
        
    def custom_context(self, request):
        """
        Custom context required for a specific report
        """
        # should be overridden
        return {}
    
    def get_context(self, request):
        """
        Specific data to be included in a report
        """
        if not self._context:
            self._context = {"slug": self.slug}
            self._context.update(self.shared_context(request))
            self._context.update(self.custom_context(request))
        return self._context