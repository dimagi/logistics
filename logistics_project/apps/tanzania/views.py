import json
from datetime import datetime
from logistics.decorators import place_in_request
from logistics.models import SupplyPoint, Product
from collections import defaultdict
from django.db.models.query_utils import Q
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from logistics_project.apps.tanzania.reports import SupplyPointStatusBreakdown
from logistics_project.apps.tanzania.tables import SupervisionTable, RandRReportingHistoryTable, NotesTable, StockOnHandTable, ProductStockColumn, ProductMonthsOfStockColumn, RandRStatusTable, DeliveryStatusTable
from logistics_project.apps.tanzania.utils import chunks, get_user_location, \
    soh_on_time_reporting, latest_status, randr_on_time_reporting, \
    submitted_to_msd
from logistics_project.apps.tanzania.tasks import send_reporting_group_list_sms, send_facility_list_sms, \
    send_region_list_sms, send_district_list_sms
from rapidsms.contrib.locations.models import Location
from logistics.tables import FullMessageTable
from models import DeliveryGroups, SupplyPointStatusValues
from logistics.views import MonthPager
from django.core.urlresolvers import reverse
from django.conf import settings
from logistics_project.apps.tanzania.decorators import gdata_required, require_superuser, require_system_admin
import gdata.docs.client
import gdata.gauth
from django.contrib import messages
from django.http import HttpResponseRedirect, HttpResponse
from dimagi.utils.parsing import string_to_datetime, string_to_boolean
from django.views.decorators.http import require_POST
from django.views import i18n as i18n_views
from django.utils.translation import ugettext as _
from logistics_project.decorators import magic_token_required
from logistics_project.apps.tanzania.forms import AdHocReportForm,\
    UploadFacilityFileForm, SupervisionDocumentForm, SMSFacilityForm
from logistics_project.apps.tanzania.models import AdHocReport, SupplyPointNote, SupplyPointStatusTypes, SupervisionDocument
from rapidsms.contrib.messagelog.models import Message
from dimagi.utils.decorators.profile import profile
from logistics_project.apps.tanzania.models import NoDataError
import os
from logistics_project.apps.tanzania.reporting.models import *
from warehouse.models import ReportRun
from warehouse.runner import update_warehouse
from warehouse.tasks import update_warehouse_async
from django_tablib.base import mimetype_map
from logistics_project.apps.tanzania.loader import get_facility_export,\
    load_locations
import mimetypes
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied
from django.utils import simplejson


PRODUCTS_PER_TABLE = 100 #7


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

def _is_national(location):
    return location and location.type.name == "REGION"

def _are_not_related(location, user_loc):
    # if no user location is specified, then they're "related"
    if not user_loc:  return False
        
    # make sure the user_loc is a parent of the other, or vice versa
    def is_eventual_parent(loc, parent_candiate):
        while loc.parent is not None:
            if parent_candiate == loc.parent: return True
            loc = loc.parent
    
    return location != user_loc \
           and not is_eventual_parent(location, user_loc) \
           and not is_eventual_parent(user_loc, location)

def get_facilities_and_location(request):
    
    def _filter_facilities_by_location(facilities, location):
        if _is_region(location):
            return facilities.filter(Q(supplied_by__location__parent_id=location.id) | Q(supplied_by__location=location))
        elif _is_district(location):
            return facilities.filter(supplied_by__location=location)
        return facilities
    
    base_facilities = SupplyPoint.objects.filter(active=True, type__code="facility")
    
    user_loc = get_user_location(request.user)
    
    # filter initial list by location
    filtered_facilities = _filter_facilities_by_location(base_facilities, 
                                                         user_loc)
    
    if request.location:
        if _are_not_related(request.location, user_loc):
            messages.error(request, "You don't have permission to view that. Location reset.")
            location = user_loc
        else:    
            location = request.location
            filtered_facilities = _filter_facilities_by_location(filtered_facilities, request.location)
        
    elif user_loc:
        location = user_loc
    else:
        location = Location.objects.get(name="MOHSW")
    request.location = location
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

def district_supply_points_below(location, sps):
    if _is_district(location):
        return [SupplyPoint.objects.get(location=location)]
    elif _is_region(location):
        return sps.filter(location__parent_id=location.id, location__type__name="DISTRICT")
    else:
        return sps.filter(location__type__name="DISTRICT")


@place_in_request()
def reports_shared(request, slug=None):
    from logistics_project.apps.tanzania.reportcalcs import new_reports as warehouse_reports
    return warehouse_reports(request, slug=slug)

@place_in_request()
def export_report(request, slug=None):
    from logistics_project.apps.tanzania.reportcalcs import export_new_report
    return export_new_report(request, slug=slug)


def get_org(request):
    org = request.GET.get('place')
    if not org:
        if request.user.get_profile() is not None:
            if request.user.get_profile().location is not None:
                org = request.user.get_profile().location.code
            elif request.user.get_profile().supply_point is not None:
                org = request.user.get_profile().supply_point.code
    if not org:
        # TODO: Get this from config
        org = 'MOHSW-MOHSW'

    return org


@place_in_request()
def dashboard(request):
    mp = MonthPager(request)

    org = get_org(request)

    # TODO: don't use location like this (district summary)
    location = Location.objects.get(code=org)

    try:
        org_summary = OrganizationSummary.objects.filter(date__range=(mp.begin_date,mp.end_date),
                                                         supply_point__code=org)
        if len(org_summary) > 0:
            org_summary = org_summary[0]
        else:
            raise NoDataError
    except NoDataError:
        return render_to_response("%s/no_data.html" % getattr(settings, 'REPORT_FOLDER'), 
                              {"month_pager": mp,
                               "graph_width": 300, # used in pie_reporting_generic
                               "graph_height": 300,
                               "location": location,
                               "destination_url": "tz_dashboard"
                               }, context_instance=RequestContext(request))

    total = org_summary.total_orgs
    avg_lead_time = org_summary.average_lead_time_in_days
    if avg_lead_time:
        avg_lead_time = "%.1f" % avg_lead_time

    soh_data = GroupSummary.objects.get(title=SupplyPointStatusTypes.SOH_FACILITY,
                                        org_summary=org_summary)
    rr_data = GroupSummary.objects.get(title=SupplyPointStatusTypes.R_AND_R_FACILITY,
                                       org_summary=org_summary)
    delivery_data = GroupSummary.objects.get(title=SupplyPointStatusTypes.DELIVERY_FACILITY,
                                             org_summary=org_summary)
    dg = DeliveryGroups(month=mp.end_date.month)

    submitting_group = dg.current_submitting_group(month=mp.end_date.month)
    processing_group = dg.current_processing_group(month=mp.end_date.month)
    delivery_group = dg.current_delivering_group(month=mp.end_date.month)

    soh_json = convert_data_to_pie_chart(soh_data, mp.begin_date)
    rr_json = convert_data_to_pie_chart(rr_data, mp.begin_date)
    delivery_json = convert_data_to_pie_chart(delivery_data, mp.begin_date)
    
    processing_numbers = prepare_processing_info([total, rr_data, delivery_data])

    product_availability = ProductAvailabilityData.objects.filter(date__range=(mp.begin_date,mp.end_date), supply_point__code=org).order_by('product__sms_code')
    product_dashboard = ProductAvailabilityDashboardChart()

    product_json = convert_product_data_to_stack_chart(product_availability, product_dashboard)

    return render_to_response("tanzania/dashboard.html",
                              {"month_pager": mp,
                               "soh_json": soh_json,
                               "rr_json": rr_json,
                               "delivery_json": delivery_json,
                               "processing_total": processing_numbers['total'],
                               "processing_complete": processing_numbers['complete'],
                               "submitting_total": rr_data.total,
                               "submitting_complete": rr_data.complete,
                               "delivery_total": delivery_data.total,
                               "delivery_complete": delivery_data.complete,
                               "delivery_group": delivery_group,
                               "submitting_group": submitting_group,
                               "processing_group": processing_group,
                               "total": total,
                               "avg_lead_time": avg_lead_time,
                               "product_json": product_json,
                               "chart_info": product_dashboard,
                               "graph_width": 300, # used in pie_reporting_generic
                               "graph_height": 300,
                               "location": location,
                               "destination_url": "tz_dashboard"
                               },
                               
                              context_instance=RequestContext(request))


@place_in_request()
def alerts(request):
    mp = MonthPager(request)
    org = get_org(request)
    location = Location.objects.get(code=org)

    alerts = Alert.objects.filter(
        supply_point__code=org,
        date__lte=mp.end_date,
        expires__lte=mp.end_date
    ).order_by('-id')

    return render_to_response(
        "tanzania/alerts.html",
        {
            "month_pager": mp,
            "location": location,
            "alerts": alerts,
            "destination_url": "tz_alerts"
        },
        context_instance=RequestContext(request)
    )


def has_nonzero_key(json, key):
    return json.has_key(key) and json[key]

def convert_data_to_pie_chart(data, date):
    chart_config = { 
        'on_time': {
            'color': 'green',
            'display': 'Submitted On Time'
        }, 
        'late': {
            'color': 'orange',
            'display': 'Submitted Late'
        }, 
        'not_submitted': {
            'color': 'red',
            'display': "Haven't Submitted "
        }, 
        'del_received': {
            'color': 'green',
            'display': 'Delivery Received',
        }, 
        'del_not_received': {
            'color': 'red',
            'display': 'Delivery Not Received',
        }, 
        'sup_received': {
            'color': 'green',
            'display': 'Supervision Received',
        }, 
        'sup_not_received': {
            'color': 'red',
            'display': 'Supervision Not Received',
        }, 
        'not_responding': {
            'color': '#8b198b',
            'display': "Didn't Respond"
        }, 
    }
    vals_config = {
        SupplyPointStatusTypes.SOH_FACILITY: 
            ['on_time', 'late', 'not_submitted', 'not_responding'],
        SupplyPointStatusTypes.DELIVERY_FACILITY: 
            ['del_received', 'del_not_received', 'not_responding'],
        SupplyPointStatusTypes.R_AND_R_FACILITY: 
            ['on_time', 'late', 'not_submitted', 'not_responding'],
        SupplyPointStatusTypes.SUPERVISION_FACILITY: 
            ['sup_received', 'sup_not_received', 'not_responding']
    }
    ret = []
    for key in vals_config[data.title]:
        if getattr(data, key, None):
            entry = {}
            entry['value'] = getattr(data, key)
            entry['color'] = chart_config[key]['color']
            entry['display'] = chart_config[key]['display']
            entry['description'] = "(%s) %s (%s)" % \
                (entry['value'], entry['display'], date.strftime("%b %Y"))
            ret.append(entry)
    return ret


def prepare_processing_info(data):
    numbers = {}
    numbers['total'] = data[0] - (data[1].total + data[2].total)
    numbers['complete'] = 0
    return numbers 

def convert_product_data_to_stack_chart(data, chart_info):
    ret_json = {}
    ret_json['ticks'] = []
    ret_json['data'] = []
    count = 0
    for product in data:
        count += 1
        ret_json['ticks'].append([count, '<span title=%s>%s</span>' % (product.product.name, product.product.code.lower())])
    for k in ['Stocked out', 'Not Stocked out', 'No Stock Data']:
        count = 0
        datalist = []
        for product in data:
            count += 1
            if k=='No Stock Data':
                datalist.append([count, product.without_data])
            elif k=='Stocked out':
                datalist.append([count, product.without_stock])
            elif k=='Not Stocked out':
                datalist.append([count, product.with_stock])
        ret_json['data'].append({'color':chart_info.label_color[k], 'label':k, 'data': datalist })
    ret_json['ticks'] = json.dumps(ret_json['ticks'])
    ret_json['data'] = json.dumps(ret_json['data'])
    return ret_json

def convert_product_data_to_sideways_chart(data, chart_info):
    ret_json = {}
    codes = []
    for d in data:
        name = str(d.product.name)
        code = str(d.product.sms_code)
        ret_json[code] = {'product': name, 'code': code, 'total': d.total, 'with_stock': d.with_stock, 'without_stock': d.without_stock, 'without_data': d.without_data, 'tick': '<span title=%s>%s</span>' % (name, code)}
        codes.append(code)

    bar_data = [{"data" : [],
                 "label": "Stocked out",
                 "bars": { "show" : "true"},
                 "color": "#a30808",
                },
                {"data" : [],
                 "label": "Not Stocked out",
                 "bars": { "show" : "true"},
                 "color": "#7aaa7a",
                },
                {"data" : [],
                 "label": "No Stock Data",
                 "bars": { "show" : "true"},
                 "color": "#efde7f",
                }]

    return ret_json, codes, bar_data

def datespan_to_month(datespan):
    return datespan.startdate.month

def _generate_soh_tables(request, facs, mp, products=None):
    show = request.GET.get('show', "")
    if not products: products = Product.objects.all().order_by('sms_code')
    product_set = chunks(products, PRODUCTS_PER_TABLE)
    tables = []
    iter = list(chunks(products, PRODUCTS_PER_TABLE))
    for prods in iter: # need a new generator
        # Need to create all the tables first.
        tables += [StockOnHandTable(object_list=facs.select_related(), request=request, prefix="soh_"+prods[0].sms_code, month=mp.month, year=mp.year, order_by=["D G", "Facility Name"])]

    for count in enumerate(iter):
        t = tables[count[0]]
        for prod in count[1]:
            if show == "months":
                pc = ProductMonthsOfStockColumn(prod, mp.month, mp.year)
            else:
                pc = ProductStockColumn(prod, mp.month, mp.year)
            t.add_column(pc, "pc_"+prod.sms_code)
    return tables, products, product_set, show

def _generate_soh_tables2(request, facs, mp, products=None):
    show = request.GET.get('show', "")
    if not products: products = Product.objects.all().order_by('sms_code')
    product_set = products
    tables = [StockOnHandTable(object_list=facs.select_related(), request=request, month=mp.month, year=mp.year, order_by=["D G", "Facility Name"])]

    # for count in enumerate(iter):
    #     t = tables[count[0]]
    #     for prod in count[1]:
    #         if show == "months":
    #             pc = ProductMonthsOfStockColumn(prod, mp.month, mp.year)
    #         else:
    #             pc = ProductStockColumn(prod, mp.month, mp.year)
    #         t.add_column(pc, "pc_"+prod.sms_code)
    return tables, products, product_set, show


@place_in_request()
def facilities_index(request):
    facs, location = get_facilities_and_location(request)
    mp = MonthPager(request)
    
    # hack - don't show nationally scoped data because it's too slow
    if location.code == settings.COUNTRY:
        tables, products, product_set, show = [None, None, None, None]
    else:
        tables, products, product_set, show = _generate_soh_tables(request, facs, mp)

    return render_to_response("tanzania/facilities_list.html",
                              {'facs': facs,
                               'product_set': product_set,
                               'products': products,
                               'tables': tables,
                               'location': location,
                               'month_pager': mp,
                               'show': show,
                               'districts': _user_districts(request.user),
                               "regions": _user_regions(request.user),
                               "destination_url": "facilities_index"
                               }, context_instance=RequestContext(request))
@place_in_request()
def facilities_ordering(request):
    facs, location = get_facilities_and_location(request)
    mp = MonthPager(request)
    return render_to_response(
        "tanzania/facilities_ordering.html",
        {
            "month_pager": mp,
            "districts": _user_districts(request.user),
            "regions": _user_regions(request.user),
            "location": location,
            "destination_url": "ordering"
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
            "notes_table": NotesTable(object_list=SupplyPointNote.objects.filter(supply_point=facility).order_by("-date").select_related(), request=request),
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


def supervision(request):
    if request.method == 'POST':
        if request.user.is_superuser:
            form = SupervisionDocumentForm(request.POST, request.FILES)
            if form.is_valid():
                newdoc = SupervisionDocument(document=request.FILES['document'])
                newdoc.save()
        else:
            raise PermissionDenied

    files = SupervisionDocument.objects.all()

    return render_to_response(
        "tanzania/supervision-docs.html", {
            "files": files,
            "form": SupervisionDocumentForm(),
        }, context_instance=RequestContext(request))


@require_superuser
def delete_supervision_doc(request, document_id):
    doc = SupervisionDocument.objects.get(id=document_id)
    doc.delete()
    return redirect('supervision')


def download_supervision_doc(request, document_id):
    doc = SupervisionDocument.objects.get(id=document_id)
    response = HttpResponse(doc.document)

    type, encoding = mimetypes.guess_type(doc.filename())

    if type is None:
        type = 'application/octet-stream'

    response['Content-Type'] = type

    if encoding is not None:
        response['Content-Encoding'] = encoding

    response['Content-Disposition'] = 'attachment; filename=%s' % doc.filename()
    return response


def facilities_by_district(request):
    """
    http://stackoverflow.com/questions/3233850/django-jquery-cascading-select-boxes
    """
    ret = []
    try:
        district = Location.objects.get(id=request.GET.get('district_id'))

        if district:
            for facility in district.get_children():
                ret.append(dict(id=facility.id, value=unicode(facility)))
            if len(ret) != 1:
                ret.insert(0, dict(id='', value=''))
    except Exception:
        # this catches user reselecting empty district
        pass

    return HttpResponse(simplejson.dumps(ret),
                        content_type='application/json')


@require_system_admin
def sms_broadcast(request):
    if request.method == "POST":
        form = SMSFacilityForm(request.POST)
        if form.is_valid():
            select_type = form.cleaned_data['recipient_select_type']

            group_a = 'A' if form.cleaned_data['group_a'] else None
            group_b = 'B' if form.cleaned_data['group_b'] else None
            group_c = 'C' if form.cleaned_data['group_c'] else None

            regions = form.cleaned_data['regions']
            districts = form.cleaned_data['districts']
            facilities = form.cleaned_data['facilities']

            message = form.cleaned_data['message']

            if select_type == 'groups':
                # remove any groups that weren't selected out
                group_list = filter(None, [group_a, group_b, group_c])
                send_reporting_group_list_sms.delay(group_list, message)
            elif select_type == 'regions':
                send_region_list_sms.delay(regions, message)
            elif select_type == 'districts':
                send_district_list_sms.delay(districts, message)
            elif select_type == 'facilities':
                send_facility_list_sms.delay(facilities, message)

            # don't leave the data on the page to prevent
            # an accidental double send
            form = SMSFacilityForm()
    else:
        form = SMSFacilityForm()

    return render_to_response(
        "tanzania/sms_broadcast.html", {
            'form': form,
        }, context_instance=RequestContext(request)
    )


def training(request):
    if request.method == "GET":

        latest_run_time = None
        latest_incomplete_time = None

        latest_run = ReportRun.objects.filter(complete=True).order_by('-id')
        incomplete_runs = ReportRun.objects.filter(complete=False).order_by('-id')

        if len(latest_run) > 0:
            latest_run_time = latest_run[0].start_run

        is_running = len(incomplete_runs) > 0
        if is_running:
            latest_incomplete_time = incomplete_runs[0].start_run

        files = []
        docs = os.listdir(getattr(settings, 'TRAINING_DOCS_FOLDER'))
        
        for doc in docs:
            item = {}
            item['link'] = doc
            item['name'] =  ' '.join(doc.split('.')[0].split('_'))
            files.append(item)
            
        form = UploadFacilityFileForm()
        return render_to_response("tanzania/training.html", {
            'is_running': is_running,
            'latest_run_time': latest_run_time,
            'latest_incomplete_time': latest_incomplete_time,
            'files': files,
            'form': form
            }, context_instance=RequestContext(request))
    
    update_warehouse_async.delay()
    return HttpResponseRedirect(reverse("training"))

def download_facilities(request):
    response = HttpResponse(mimetype=mimetype_map.get(format, 'application/octet-stream'))
    response['Content-Disposition'] = 'attachment; filename=tanzania-facilities.csv'
    get_facility_export(response)
    return response

@require_POST
def upload_facilities(request):
    form = UploadFacilityFileForm(request.POST, request.FILES)
    if form.is_valid():
        f = request.FILES['file']
        try: 
            msgs = load_locations(f)
            for m in msgs:
                messages.info(request, m)
        except Exception, e:
            messages.error(request, "Something went wrong with that upload. " 
                           "Please double check the file format or "
                           "try downloading a new copy. Your error message"
                           "is %s" % e)
    else:
        messages.error(request, "Please select a file")    
    return HttpResponseRedirect(reverse("training"))


