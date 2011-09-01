from logistics.decorators import place_in_request
from logistics.models import SupplyPoint, Product
from django.db.models.query_utils import Q
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from logistics_project.apps.tanzania.reports import SupplyPointStatusBreakdown
from logistics_project.apps.tanzania.tables import OrderingStatusTable, SupervisionTable, RandRReportingHistoryTable, NotesTable
from logistics_project.apps.tanzania.utils import chunks, get_user_location, soh_on_time_reporting, latest_status, randr_on_time_reporting
from rapidsms.contrib.locations.models import Location
from logistics.tables import FullMessageTable
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
from logistics_project.apps.tanzania.forms import AdHocReportForm
from logistics_project.apps.tanzania.models import AdHocReport, SupplyPointNote, SupplyPointStatusTypes
from rapidsms.contrib.messagelog.models import Message

PRODUCTS_PER_TABLE = 12

def tz_location_url(location):
    try:
        sp = SupplyPoint.objects.get(location=location)
        if sp.type.code == "facility":
            return reverse("tz_facility_details", args=(sp.pk,))
    except SupplyPoint.DoesNotExist:
        pass
    return ""

def _is_district(location):
    return location and location.type.name == "DISTRICT"

def _is_region(location):
    return location and location.type.name == "REGION"

def _get_facilities_and_location(request):
    
    def _filter_facilities_by_location(facilities, location):
        if _is_region(location):
            return facilities.filter(Q(supplied_by__location__parent_id=location.id) | Q(supplied_by__location=location))
        elif _is_district(location):
            return facilities.filter(supplied_by__location=location)
        return facilities
    
    base_facilities = SupplyPoint.objects.filter(active=True, type__code="facility")
    # filter initial list by location
    filtered_facilities = _filter_facilities_by_location(base_facilities, 
                                                         get_user_location(request.user))
    if request.location:
        location = request.location
        filtered_facilities = _filter_facilities_by_location(filtered_facilities, request.location)
    else:
        location = Location.objects.get(name="MOHSW")
    return (filtered_facilities, location)

def _districts():
    return Location.objects.filter(type__name="DISTRICT")

def _regions():
    return Location.objects.filter(type__name="REGION")

def _user_districts(user):
    districts = _districts()
    location = get_user_location(user)
    if _is_district(location):
        return districts.filter(pk=location.pk)
    elif _is_region(location):
        return districts.filter(parent_id=location.pk)
    return districts

def _user_regions(user):
    regions = _regions()
    location = get_user_location(user)
    if _is_district(location):
        return regions.filter(pk=location.parent.pk)
    elif _is_region(location):
        return regions.filter(pk=location.pk)
    return regions
    
@place_in_request()
def dashboard(request):
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
                               "districts": _user_districts(request.user),
                               "regions": _user_regions(request.user),
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
                               'districts': _user_districts(request.user),
                               "regions": _user_regions(request.user),
                               }, context_instance=RequestContext(request))
@place_in_request()
def facilities_ordering(request):
    facs, location = _get_facilities_and_location(request)
    mp = MonthPager(request)
    return render_to_response(
        "tanzania/facilities_ordering.html",
        {
            "month_pager": mp,
            "districts": _user_districts(request.user),
            "regions": _user_regions(request.user),
            "location": location,
            "table": OrderingStatusTable(object_list=facs, request=request, month=mp.month, year=mp.year)
        },
        context_instance=RequestContext(request))

def facility_details(request, facility_id):
    facility = get_object_or_404(SupplyPoint, pk=facility_id)

    if request.method == "POST":
        text = request.POST.get('note_text')
        if text:
            note = SupplyPointNote(supply_point=facility,
                                   user=request.user,
                                   text=text)
            note.save()
            messages.success(request, "Note added!")

    return render_to_response(
        "tanzania/facility_details.html",
        {
            "facility": facility,
            "randr_status": latest_status(facility, SupplyPointStatusTypes.R_AND_R_FACILITY),
            "notes_table": NotesTable(object_list=SupplyPointNote.objects.filter(supply_point=facility).order_by("-date"), request=request),
            "report_types": ['Stock on Hand', 'Months of Stock']
        },
        context_instance=RequestContext(request))

def facility_messages(request, facility_id):
    facility = get_object_or_404(SupplyPoint, pk=facility_id)
    return render_to_response("tanzania/facility_messages.html",
        {
            "facility": facility,
            "table": FullMessageTable(object_list=Message.objects.filter(contact__in=facility.contact_set.all).order_by("-date"), request=request)
        },
                              context_instance=RequestContext(request)
    )

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
    dg = DeliveryGroups(mp.month, facs=facs)
    bd = SupplyPointStatusBreakdown(facs, mp.year, mp.month)
    ot = randr_on_time_reporting(dg.submitting(), mp.year, mp.month)
    products = Product.objects.all().order_by('name')
    product_set = chunks(products, PRODUCTS_PER_TABLE)
    return render_to_response("tanzania/reports.html",
        {
          "location": location,
          "month_pager": mp,
          "districts": _user_districts(request.user),
          "regions": _user_regions(request.user),
          "facs": facs,
          "product_set": product_set,
          "products": products,
          "dg": dg,
          "bd": bd,
          "on_time": ot,
          "reporting_percentage": (float(len(bd.submitted)) / float(len(dg.submitting())) * 100) if len(dg.submitting()) else 0.0,
          "on_time_percentage": (float(len(ot)) / float(len(bd.submitted)) * 100) if len(bd.submitted) else 0.0,
          "supervision_table": SupervisionTable(object_list=dg.submitting(), request=request,
                                                month=mp.month, year=mp.year),
          "randr_table": RandRReportingHistoryTable(object_list=dg.submitting(), request=request,
                                                    month=mp.month, year=mp.year),
        },
        context_instance=RequestContext(request))

@place_in_request()
def supervision(request):
    facs, location = _get_facilities_and_location(request)
    mp = MonthPager(request)
    dg = DeliveryGroups(mp.month, facs=facs)
    return render_to_response("tanzania/supervision.html",
        {
          "location": location,
          "month_pager": mp,
          "districts": _user_districts(request.user),
          "regions": _user_regions(request.user),
          "facs": dg.submitting(facs, month=mp.month),
          "dg": dg,
          "bd": SupplyPointStatusBreakdown(facs, mp.year, mp.month),
          "supervision_table": SupervisionTable(object_list=dg.submitting(facs, month=mp.month), request=request,
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
                report.send()
                messages.success(request, "Test report sent to %s" % ", ".join(report.get_recipients()))
                
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
    

