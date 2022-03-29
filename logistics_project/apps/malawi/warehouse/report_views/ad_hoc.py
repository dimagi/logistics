from builtins import object
from logistics_project.apps.malawi.warehouse import warehouse_view
from logistics.models import SupplyPoint, ProductReport, Product
from logistics_project.apps.malawi.util import get_default_supply_point,\
    hsa_supply_points_below
from logistics_project.utils.dates import first_of_next_month
import itertools
from logistics_project.apps.malawi.warehouse.report_views.consumption_profiles import consumption_row

class SubReport(object):

    def __init__(self, slug, name, context_function, template_name):
        self.slug = slug
        self.name = name
        self.context_function = context_function
        self.template_name = template_name

    @property
    def template(self):
        return 'malawi/new/reports/adhoc/%s' % self.template_name


class View(warehouse_view.DashboardView):
    """
    Ad hoc reports - superuser only
    """
    show_report_nav = False

    def can_view(self, request):
        return request.user.is_superuser
        
    def custom_context(self, request):
        subreports = [
            SubReport('hc-requests', 'Requests per HC', hc_context, 'hc-reqs.html'),
            SubReport('amc-averages', 'AMC per period', amc_context, 'amc-averages.html'),
        ]
        context = {
            'subreports': subreports,
        }

        subreport_slug = request.GET.get('subreport')
        subreport = None
        if subreport_slug:
            for sr in subreports:
                if sr.slug == subreport_slug:
                    subreport = sr
                    break
            assert subreport is not None, 'bad subreport %s' % subreport_slug
            context.update(subreport.context_function(request))

        context['subreport'] = subreport
        return context

def hc_context(request):
    """
    The second request is to get the number of requests per HC for the month
    of December. I can get reporting rates but it only shows one report per HSA
    - i.e. it is a %. We wanted to know total number of reports including
    situations where an HSA might report twice in one month (not duplicates on
    same day but for example one at the beginning of the month and one a few
    weeks later). This one might be complicated so let me know if it is
    possible.
    """
    sp = SupplyPoint.objects.get(location=request.location) \
        if request.location else get_default_supply_point(request.user)

    hsas = hsa_supply_points_below(sp.location).order_by('code')
    end_date = first_of_next_month(request.datespan.enddate)

    def _reports_for_hsa(hsa):
        reports = ProductReport.objects.filter(
            report_type__code='soh',
            supply_point=hsa,
            report_date__gte=request.datespan.startdate,
            report_date__lt=end_date).order_by('message')
        # this is super painfully slow
        last_message = None
        filtered_reports = []
        for pr in reports:
            if pr.message == last_message:
                continue
            else:
                last_message = pr.message
                filtered_reports.append(pr)
        return [[hsa.supplied_by.name, hsa.supplied_by.code, hsa.name, hsa.code, report.report_date] \
                for report in filtered_reports]
    
    table = {
        "id": "main-table",
        "is_datatable": False,
        "is_downloadable": True,
        "header": ["Health Center", "HC Code", "HSA", "HSA Code", "Report Date"],
        "data": itertools.chain(*[_reports_for_hsa(hsa) for hsa in hsas]),
    }

    return {
        'table': table,
    }

def amc_context(request):
    """
    AMC for Nov and Dec period for all HSAs in the list attached. The last
    column in the consumption profiles report is is the information we require.
    """
    sp = SupplyPoint.objects.get(location=request.location) \
        if request.location else get_default_supply_point(request.user)

    hsas = hsa_supply_points_below(sp.location).order_by('code')
    products = Product.objects.all()

    def _rows_for_hsa(hsa):
        rows = [consumption_row(hsa, p, request.datespan) for p in products]
        return [[hsa.name, hsa.code, row[0], row[1], row[5], row[6]] for row in rows]

    table = {
        "id": "main-table",
        "is_datatable": False,
        "is_downloadable": True,
        "header": ["HSA", "HSA Code", "Product", "Total Consumption",
                   "Total Adjusted Consumption", "AMC"],
        "data": itertools.chain(*[_rows_for_hsa(hsa) for hsa in hsas]),
    }

    return {
        'table': table,
    }
