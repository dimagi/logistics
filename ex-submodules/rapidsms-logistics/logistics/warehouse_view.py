from django.conf import settings


class WarehouseView(object):
    """
    View class to be extended for each report page 
        with its own get_context method
    
    Include in settings:

        REPORT_LIST = SortedDict([
        ("Dashboard", "dashboard"),])
    """
    
    def __init__(self, request, slug):
        self.context = self.shared_context(request)
        self.context.update(self.get_context(request))

    def shared_context(self, request):
        """
        Add this to your subclasses shared_context method:

        base_context = super(<YourWarehouseViewSubclass>, self).shared_context(request)
        """
        to_stub = lambda x: {"name": x, "slug": settings.REPORT_LIST[x]}
        stub_reports = [to_stub(r) for r in settings.REPORT_LIST.keys()]

        return { 
            "report_list": stub_reports,
            "settings": settings,
        }

    def get_context(self, request):
        """
        Specific data to be included in a report
        """
        pass