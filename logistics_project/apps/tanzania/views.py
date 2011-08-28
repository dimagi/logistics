from logistics.decorators import place_in_request
from logistics.models import SupplyPoint, Product
from django.db.models.query_utils import Q
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from django.utils import translation
from logistics_project.apps.tanzania.reports import SupplyPointStatusBreakdown
from logistics_project.apps.tanzania.tables import OrderingStatusTable, SupervisionTable, RandRReportingHistoryTable
from logistics_project.apps.tanzania.utils import chunks
from rapidsms.contrib.locations.models import Location
from models import DeliveryGroups
from logistics.views import MonthPager
from django.core.urlresolvers import reverse
from django.conf import settings
from logistics_project.apps.tanzania.decorators import gdata_required
import gdata.docs.client
import gdata.gauth
from django.contrib import messages
from django.http import HttpResponseRedirect, HttpResponse
from dimagi.utils.parsing import string_to_datetime
from django.views.decorators.http import require_POST
from django.views import i18n as i18n_views
from django.utils.translation import ugettext as _
from logistics_project.decorators import magic_token_required
from logistics_project.apps.tanzania.tasks import email_report
from logistics_project.apps.tanzania.forms import AdHocReportForm
from logistics_project.apps.tanzania.models import AdHocReport

PRODUCTS_PER_TABLE = 15

def tz_location_url(location):
    try:
        sp = SupplyPoint.objects.get(location=location)
        if sp.type.code == "facility":
            return reverse("tz_facility_details", args=(sp.pk,))
    except SupplyPoint.DoesNotExist:
        pass
    return ""

def _get_facilities_and_location(request):
    base_facilities = SupplyPoint.objects.filter(active=True, type__code="facility")

    # district filter
    if request.location:
        location = request.location
        if request.location.type.name == "REGION":
            base_facilities = base_facilities.filter(Q(supplied_by__location__parent_id=location.id) | Q(supplied_by__location=location))
        elif request.location.type.name == "DISTRICT":
            base_facilities = base_facilities.filter(supplied_by__location=location)
    else:
        location = Location.objects.get(name="MOHSW")
    return base_facilities, location

def _districts():
    return Location.objects.filter(type__name="DISTRICT")
def _regions():
    return Location.objects.filter(type__name="REGION")

@place_in_request()
def dashboard(request):
    translation.activate("en")
    mp = MonthPager(request)
    base_facilities, location = _get_facilities_and_location(request)

    dg = DeliveryGroups(mp.month, facs=base_facilities)
    sub_data = SupplyPointStatusBreakdown(base_facilities, month=mp.month, year=mp.year)
    return render_to_response("tanzania/dashboard.html",
                              {
                               "sub_data": sub_data,
                               "graph_width": 300,
                               "graph_height": 300,
                               "dg": dg,
                               "month_pager": mp,
                               "facs": list(base_facilities), # Not named 'facilities' so it won't trigger the selector
                               "districts": _districts(),
                               "regions": _regions(),
                               "location": location},
                               
                              context_instance=RequestContext(request))

def datespan_to_month(datespan):
    return datespan.startdate.month

#@login_required
@place_in_request()
def facilities_index(request):
    # Needs ability to view stock as of a given month.
    facs, location = _get_facilities_and_location(request)
    mp = MonthPager(request)
    products = Product.objects.all().order_by('name')
    product_set = chunks(products, PRODUCTS_PER_TABLE)
    return render_to_response("tanzania/facilities_list.html",
                              {'facs': facs,
                               'product_set': product_set,
                               'products': products,
                               'location': location,
                               'month_pager': mp,
                               'districts': _districts(),
                               "regions": _regions(),
                               }, context_instance=RequestContext(request))
@place_in_request()
def facilities_ordering(request):
    facs, location = _get_facilities_and_location(request)
    mp = MonthPager(request)
    return render_to_response(
        "tanzania/facilities_ordering.html",
        {
            "month_pager": mp,
            "districts": _districts(),
            "regions": _regions(),
            "location": location,
            "table": OrderingStatusTable(object_list=facs, request=request, month=mp.month, year=mp.year)
        },
        context_instance=RequestContext(request))

def facility_details(request, facility_id):
    facility = get_object_or_404(SupplyPoint, pk=facility_id)
    return render_to_response(
        "tanzania/facility_details.html",
        {
            "facility": facility,
            "report_types": ['Stock on Hand', 'Months of Stock']
        },
        context_instance=RequestContext(request))

@gdata_required
def docdownload(request, facility_id):
    """
    Download google docs document
    """
    if 'token' in request.session:
        #should be able to make this global
        client = gdata.docs.client.DocsClient()
        client.ssl = True  # Force all API requests through HTTPS
        client.http_client.debug = False  # Set to True for debugging HTTP requests
        client.auth_token = gdata.gauth.AuthSubToken(request.session['token'])
        supply_point = get_object_or_404(SupplyPoint, pk=facility_id)
        query_string = '/feeds/default/private/full?title=%s&title-exact=false&max-results=100' % supply_point.code
        feed = client.GetDocList(uri=query_string)

        most_recent_doc = None

        if not feed.entry:
            messages.error(request, 'Sorry, there is no recent R&R for this facility.')
            return HttpResponseRedirect(reverse("tz_facility_details", args=[supply_point.pk]))
        else:
            for entry in feed.entry:
                if not most_recent_doc:
                    most_recent_doc = entry
                else:
                    new_date = string_to_datetime(entry.updated.text)
                    old_date = string_to_datetime(most_recent_doc.updated.text)
                    if new_date > old_date:
                        most_recent_doc = entry

        exportFormat = '&exportFormat=pdf'
        content = client.GetFileContent(uri=most_recent_doc.content.src + exportFormat)
    
    response = HttpResponse(content)
    response['content-Type'] = 'application/pdf'
    response['Content-Disposition'] = 'inline; filename=%s' % most_recent_doc.title.text
    return response

def change_language(request):
    return render_to_response('tanzania/change_language.html',
                              {'LANGUAGES': settings.LANGUAGES},
                              context_instance=RequestContext(request))

@require_POST
def change_language_real(request):
    messages.success(request, _("Language changed to %(lang)s") % \
                    {"lang": dict(settings.LANGUAGES)[request.POST.get("language")]})
    return i18n_views.set_language(request)

@place_in_request()
def reporting(request):
    facs, location = _get_facilities_and_location(request)
    mp = MonthPager(request)
    products = Product.objects.all().order_by('name')
    product_set = chunks(products, PRODUCTS_PER_TABLE)
    randr_facs = facs.filter(groups__code__in=DeliveryGroups(mp.month).current_submitting_group())
    return render_to_response("tanzania/reports.html",
        {
          "location": location,
          "month_pager": mp,
          "districts": _districts(),
          "regions": _regions(),
          "facs": facs,
          "product_set": product_set,
          "products": products,
          "supervision_table": SupervisionTable(object_list=facs, request=request, 
                                                month=mp.month, year=mp.year),
          "randr_table": RandRReportingHistoryTable(object_list=randr_facs, request=request, 
                                                    month=mp.month, year=mp.year),
        },
        context_instance=RequestContext(request))

@place_in_request()
@magic_token_required()
def reporting_pdf(request):
    return reporting(request)

@place_in_request()
def ad_hoc_reports(request):
    supply_point = None
    if request.location:
        try:
            supply_point = SupplyPoint.objects.get(location=request.location)
        except SupplyPoint.DoesNotExist:
            pass
    report = None
    if supply_point:
        try:
            report = AdHocReport.objects.get(supply_point=supply_point)
        except (AdHocReport.DoesNotExist, AdHocReport.MultipleObjectsReturned):
            pass
        
    if request.method == "POST":
        form = AdHocReportForm(request.POST)
        if form.is_valid():
            new_report = form.save(commit=False)
            if report is not None:
                assert(report.supply_point == new_report.supply_point)
                report.recipients = new_report.recipients
            else:
                report = new_report
            
            report.save()
            messages.success(request, "changes to ad hoc report saved")
            if request.POST["submit"] == "Send Test Messages":
                recipients = report.get_recipients()
                email_report.delay(report.supply_point.code, recipients)
                messages.success(request, "Test report sent to %s" % ", ".join(recipients))
                
            else:
                return HttpResponseRedirect("%s?place=%s" % (reverse("reports"), 
                                                             report.supply_point.code))
    
    else:
        if report:
            form = AdHocReportForm(instance=report)
        elif supply_point:
            form = AdHocReportForm({"supply_point": supply_point.pk, "recipients": "Put email addresses here, separated by commas."})
        else:
            form = AdHocReportForm()
    return render_to_response("tanzania/edit_adhoc_report.html", {
        "form": form,
    }, context_instance=RequestContext(request))
    

