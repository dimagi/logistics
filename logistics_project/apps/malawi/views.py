from datetime import datetime, date, timedelta
from urllib import urlencode
from urllib2 import urlopen
from collections import defaultdict
import logging

from django.conf import settings
from django.contrib import messages
from django.core.serializers import json
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template.context import RequestContext
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.vary import vary_on_cookie
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.models import User as auth_user
from django.contrib.auth.models import Group as auth_group
from django.db.models.aggregates import Count

from dimagi.utils.csv import UnicodeWriter
from dimagi.utils.dates import DateSpan, months_between, add_months
from dimagi.utils.django.permission_required import permission_required_with_403
from dimagi.utils.decorators.datespan import datespan_in_request

from rapidsms.models import Contact
from rapidsms.contrib.locations.models import Location
from rapidsms.models import Backend, Connection
from rapidsms.contrib.messagelog.models import Message

from logistics.models import SupplyPoint, Product, \
    StockTransaction, StockRequestStatus, StockRequest, ProductReport, ContactRole
from logistics.decorators import place_in_request
from logistics.charts import stocklevel_plot
from logistics.view_decorators import filter_context
from logistics.reports import ReportingBreakdown
from logistics.util import config
from logistics.charts import amc_plot

from logistics_project.apps.malawi.warehouse.report_utils import datespan_default
from logistics_project.apps.malawi.exceptions import IdFormatException
from logistics_project.apps.malawi.tables import MalawiContactTable, MalawiLocationTable, \
    MalawiProductTable, HSATable, StockRequestTable, \
    HSAStockRequestTable, DistrictTable, ConsumptionDataTable, OrganizationTable
from logistics_project.apps.malawi.util import get_districts, get_facilities, hsas_below, group_for_location, format_id, ConsumptionData, hsa_supply_points_below
from logistics_project.apps.malawi.reports import ReportInstance, ReportDefinition,\
    REPORT_SLUGS, REPORTS_CURRENT, REPORTS_LOCATION
from logistics_project.apps.malawi.models import Organization
from logistics_project.apps.malawi.forms import OrganizationForm

from static.malawi.scmgr_const import PRODUCT_CODE_MAP, HEALTH_FACILITY_MAP


def organizations(request):
    orgs = Organization.objects.all()
    table = {
        "id": "org-table",
        "is_datatable": True,
        "is_downloadable": False,
        "header": ["Name", "Members", "Managed Supply Points"],
        "data": [],
    }
    for org in orgs:
        table["data"].append({"url": "edit/%d" % org.id, "data": [org.name, org.contact_set.all().count(),
            " ".join([s.name for s in org.managed_supply_points.all()])]})

    table["height"] = min(480, (orgs.count()+1)*30)

    context = {
        "orgs": orgs,
        "table": table,
    }
    return render_to_response("%s/organizations.html" % settings.MANAGEMENT_FOLDER,
                context, context_instance=RequestContext(request))

def edit_organization(request, pk):
    org = get_object_or_404(Organization, pk=pk)
    if request.method == 'POST': 
        form = OrganizationForm(request.POST, instance=org) 
        if form.is_valid(): 
            org = form.save()
            messages.success(request, "Organization '%s' was successfully saved"  % org.name)
            return HttpResponseRedirect(reverse('malawi_organizations'))
    else:
        form = OrganizationForm(instance=org) 

    return render_to_response('malawi/edit_organization.html', {
        'form': form,
        'is_new': False
    }, context_instance=RequestContext(request))
    
def new_organization(request):
    if request.method == 'POST': 
        form = OrganizationForm(request.POST) 
        if form.is_valid(): 
            new_org = form.save()
            messages.success(request, "Organization '%s' was successfully created"  % new_org.name)
            return HttpResponseRedirect(reverse('malawi_organizations'))
    else:
        form = OrganizationForm() 

    return render_to_response('malawi/edit_organization.html', {
        'form': form,
        'is_new': True
    }, context_instance=RequestContext(request))

def contacts(request):
    contacts = Contact.objects.all()
    table = {
        "id": "contacts-table",
        "is_datatable": True,
        "is_downloadable": False,
        "header": ["Name", "Role", "HSA Id", "SupplyPoint",
                   "Phone Number", "Commodities", "Organization"],
        "data": [],
    }
    for c in contacts:
        table["data"].append({"url": "/registration/%d/edit" % c.id, "data": [c.name, 
            c.role.name if c.role else "", c.hsa_id,
            c.supply_point.name if c.supply_point else "",
            c.default_connection.identity if c.default_connection else "",
            " ".join([com.sms_code for com in c.commodities.all()]),
            c.organization.name if c.organization else ""]})

    table["height"] = min(480, (contacts.count()+1)*30)

    context = {
        "contacts": contacts,
        "table": table,
    }
    return render_to_response("%s/contacts.html" % settings.MANAGEMENT_FOLDER,
                context, context_instance=RequestContext(request))

def permissions(request):
    users = auth_user.objects.all()
    groups = auth_group.objects.all()
    table = {
        "id": "user-table",
        "is_datatable": True,
        "is_downloadable": False,
        "header": ["User", "District", "Location", "Organization", "Groups"],
        "data": [],
    }
    for u in users:
        prof = u.get_profile()
        table["data"].append([u.username, prof.supply_point, prof.location,\
            prof.organization.name if prof.organization else "",\
            " ".join([g.name for g in u.groups.all()])])

    table["height"] = min(480, (users.count()+1)*30)

    context = {
        "users": users,
        "groups": groups,
        "table": table,
    }
    return render_to_response("%s/permissions.html" % settings.MANAGEMENT_FOLDER,
                context, context_instance=RequestContext(request))

def places(request):
    locs = Location.objects.filter(is_active=True)
    table = {
        "id": "loc-table",
        "is_datatable": True,
        "is_downloadable": False,
        "header": ["Name", "Code", "Type", "Supplied By"],
        "data": [],
    }
    for loc in locs:
        sp = SupplyPoint.objects.get(location=loc)
        table["data"].append([loc.name, loc.code,
            loc.type.name if loc.type else "",
            sp.supplied_by.name if sp.supplied_by else ""])

    table["height"] = min(480, (locs.count()+1)*30)

    context = {
        "locs": locs,
        "table": table,
    }
    return render_to_response("%s/places.html" % settings.MANAGEMENT_FOLDER,
                context, context_instance=RequestContext(request))

def places_upload(request):
    if request.method == 'GET':
        upload_link = reverse("malawi_places_upload")
        return render_to_response("%s/places-upload.html" % settings.MANAGEMENT_FOLDER,
            {"upload_link": upload_link}, context_instance=RequestContext(request))

    if not request.FILES.has_key('file'):
        messages.warning(request, "No File Detected")
        return redirect(reverse("malawi_places_upload"))

    # move files around, save old one with datestamp

    f = request.FILES.get('file')
    destination = '%s/%s.%s' % (settings.STATIC_RESOURCES, f.name.split('.')[-2], 'csv')
    write_file = open(destination, 'wb+')

    for chunk in f.chunks():
        write_file.write(chunk)
    write_file.close()

    import os
    if not os.path.getsize(destination) == f.size:
        # move files around, put old one back
        messages.warning(request, "Unknown Error - Upload Failed")
        return redirect(reverse("malawi_places_upload"))

    # run malawi_init and partial runner

    return redirect(reverse("malawi_places"))

def products(request):
    prds = Product.objects.filter(is_active=True)
    table = {
        "id": "prd-table",
        "is_datatable": True,
        "is_downloadable": False,
        "header": ["Name", "SMS Code", "Avg Monthly Consumption",
                   "Emergency Order Level", "Type"],
        "data": [],
    }
    for prd in prds:
        table["data"].append([prd.name, prd.sms_code, prd.average_monthly_consumption,
            prd.emergency_order_level, prd.type.name if prd.type else ""])

    table["height"] = min(480, (prds.count()+1)*30)

    context = {
        "prds": prds,
        "table": table,
    }
    return render_to_response("%s/products.html" % settings.MANAGEMENT_FOLDER,
                context, context_instance=RequestContext(request))

def products_upload(request):
    if request.method == 'GET':
        upload_link = reverse("malawi_products_upload")
        return render_to_response("%s/products-upload.html" % settings.MANAGEMENT_FOLDER,
            {"upload_link": upload_link}, context_instance=RequestContext(request))

    if not request.FILES.has_key('file'):
        messages.warning(request, "No File Detected")
        return redirect(reverse("malawi_products_upload"))

    # move files around, save old one with datestamp

    f = request.FILES.get('file')
    destination = '%s/%s.%s' % (settings.STATIC_RESOURCES, f.name.split('.')[-2], 'csv')
    write_file = open(destination, 'wb+')

    for chunk in f.chunks():
        write_file.write(chunk)
    write_file.close()

    import os
    if not os.path.getsize(destination) == f.size:
        # move files around, put old one back
        messages.warning(request, "Unknown Error - Upload Failed")
        return redirect(reverse("malawi_products_upload"))

    # run malawi_init and partial runner

    return redirect(reverse("malawi_products"))

@datespan_default
def sms_tracking(request):
    
    class ContactCache(object):
        def __init__(self):
            self.contacts = {}
        
        def get(self, pk):
            return self.contacts[pk] if pk in self.contacts else Contact.objects.get(pk=pk)
    
    orgs = dict(zip(Organization.objects.all(), 
                    [defaultdict(lambda x: 0) for i in range(Organization.objects.count())]))

    all_messages = Message.objects.filter(date__gte=request.datespan.computed_startdate,
                                          date__lte=request.datespan.computed_enddate)
    inbound_counts = all_messages.filter(direction="I").\
                        values('contact').annotate(messages=Count("contact"))
    outbound_counts = all_messages.filter(direction="O").\
                        values('contact').annotate(messages=Count("contact"))
    
    cache = ContactCache()
    def _update(key, row):
        if row["contact"] is not None:
            contact = cache.get(row["contact"])
            if contact.organization:
                orgs[contact.organization][key] = row["messages"]
        
    for row in inbound_counts:
        _update("inbound", row)
    for row in outbound_counts:
        _update("outbound", row)

    table = {
        "id": "sms-table",
        "is_datatable": False,
        "is_downloadable": False,
        "header": ["Organization", "Inbound Messages", "Outbound Messages"],
        "data": [],
    }
    for org, vals in orgs.iteritems():
        table["data"].append([org.name, vals["inbound"] if vals.has_key("inbound") else 0, 
                            vals["outbound"] if vals.has_key("outbound") else 0])

    return render_to_response("%s/sms-tracking.html" % settings.MANAGEMENT_FOLDER,
                              {"table": table},
                              context_instance=RequestContext(request))

@datespan_default
def telco_tracking(request):
    start_date = request.datespan.computed_startdate
    end_date = request.datespan.computed_enddate

    results = []

    for year, month in months_between(start_date,end_date):
        date1 = datetime(year,month,1)
        endyear, endmonth = add_months(year,month,1)
        date2 = datetime(endyear,endmonth,1)
        tnm_msgs = Message.objects.filter(connection__backend__name__startswith='tnm',\
                date__range=(date1,date2))
        airtel_msgs = Message.objects.filter(connection__backend__name__startswith='airtel',\
                date__range=(date1,date2))
        results.append((date1, tnm_msgs.count(), airtel_msgs.count()))

    table = {
        "id": "telco-table",
        "is_datatable": False,
        "is_downloadable": True,
        "header": ["Date", "TNM", "Airtel"],
        "data": [],
    }
    for result in results:
        table["data"].append([result[0].strftime("%B, %Y"), result[1], result[2]])

    return render_to_response("%s/telco-tracking.html" % settings.MANAGEMENT_FOLDER,
                              {"table": table},
                              context_instance=RequestContext(request))

@permission_required("is_superuser")
def register_user(request, template="malawi/register-user.html"):
    context = dict()
    context['facilities'] = SupplyPoint.objects.filter(type__code="hf").order_by('code')
    context['backends'] = Backend.objects.all()
    context['dialing_code'] = settings.COUNTRY_DIALLING_CODE # [sic]
    if request.method != 'POST':
        return render_to_response(template, context, context_instance=RequestContext(request))

    id = request.POST.get("id", None)
    facility = request.POST.get("facility", None)
    name = request.POST.get("name", None)
    number = request.POST.get("number", None)
    backend = request.POST.get("backend", None)

    if not (id and facility and name and number and backend):
        messages.error(request, "All fields must be filled in.")
        return render_to_response(template, context, context_instance=RequestContext(request))
    hsa_id = None
    try:
        hsa_id = format_id(facility, id)
    except IdFormatException:
        messages.error(request, "HSA ID must be a number between 0 and 99.")
        return render_to_response(template, context, context_instance=RequestContext(request))

    try:
        parent = SupplyPoint.objects.get(code=facility)
    except SupplyPoint.DoesNotExist:
        messages.error(request, "No facility with that ID.")
        return render_to_response(template, context, context_instance=RequestContext(request))

    if Location.objects.filter(code=hsa_id).exists():
        messages.error(request, "HSA with that code already exists.")
        return render_to_response(template, context, context_instance=RequestContext(request))

    try:
        number = int(number)
    except ValueError:
        messages.error(request, "Phone number must contain only numbers.")
        return render_to_response(template, context, context_instance=RequestContext(request))

    hsa_loc = Location.objects.create(name=name, type=config.hsa_location_type(),
                                          code=hsa_id, parent=parent.location)
    sp = SupplyPoint.objects.create(name=name, code=hsa_id, type=config.hsa_supply_point_type(),
                                        location=hsa_loc, supplied_by=parent, active=True)
    sp.save()
    contact = Contact()
    contact.name = name
    contact.supply_point = sp
    contact.role = ContactRole.objects.get(code=config.Roles.HSA)
    contact.is_active = True
    contact.save()

    connection = Connection()
    connection.backend = Backend.objects.get(pk=int(backend))
    connection.identity = "+%s%s" % (settings.COUNTRY_DIALLING_CODE, number) #TODO: Check validity of numbers
    connection.contact = contact
    connection.save()

    messages.success(request, "HSA added!")

    return render_to_response(template, context, context_instance=RequestContext(request))

def help(request):
    return render_to_response("malawi/help.html", {}, context_instance=RequestContext(request))




############################
# old reports
############################


def contacts_OLD(request):
    return render_to_response("malawi/contacts.html",
        {
            "contacts_table": MalawiContactTable(Contact.objects, request=request)
        }, context_instance=RequestContext(request)
    )

def organizations_OLD(request):
    return render_to_response("malawi/organizations.html",
        {
            "organization_table": OrganizationTable(Organization.objects, request=request)
        }, context_instance=RequestContext(request)
    )

def places_OLD(request):
    return render_to_response("malawi/places.html",
        {
            "location_table": MalawiLocationTable(Location.objects.exclude(type__slug="hsa"), request=request)
        }, context_instance=RequestContext(request)
    )

def products_OLD(request):
    return render_to_response("malawi/products.html",
        {
            "product_table": MalawiProductTable(Product.objects, request=request)
        }, context_instance=RequestContext(request)
    )

@datespan_in_request()
def sms_tracking_OLD(request):
    
    class ContactCache(object):
        def __init__(self):
            self.contacts = {}
        
        def get(self, pk):
            return self.contacts[pk] if pk in self.contacts else Contact.objects.get(pk=pk)
    
    orgs = dict(zip(Organization.objects.all(), 
                    [defaultdict(lambda x: 0) for i in range(Organization.objects.count())]))

    all_messages = Message.objects.filter(date__gte=request.datespan.computed_startdate,
                                          date__lte=request.datespan.computed_enddate)
    inbound_counts = all_messages.filter(direction="I").\
                        values('contact').annotate(messages=Count("contact"))
    outbound_counts = all_messages.filter(direction="O").\
                        values('contact').annotate(messages=Count("contact"))
    
    cache = ContactCache()
    def _update(key, row):
        if row["contact"] is not None:
            contact = cache.get(row["contact"])
            if contact.organization:
                orgs[contact.organization][key] = row["messages"]
        
    for row in inbound_counts:
        _update("inbound", row)
    for row in outbound_counts:
        _update("outbound", row)

    return render_to_response("malawi/sms_tracking.html",
                              {"organizations": orgs},
                              context_instance=RequestContext(request))


#@cache_page(60 * 15)
@place_in_request()
def dashboard(request):
    
    base_facilities = SupplyPoint.objects.filter(active=True, type__code="hsa")
    em_group = None
    if request.location:
        valid_facilities = get_facilities().filter(parent_id=request.location.pk)
        base_facilities = base_facilities.filter(location__parent_id__in=[f.pk for f in valid_facilities])
        em_group = (group_for_location(request.location) == config.Groups.EM)
    # reporting info

    month = MonthPager(request)

    if em_group:
        report = ReportingBreakdown(base_facilities, month.datespan, include_late = True, MNE=False, days_for_late=settings.LOGISTICS_DAYS_UNTIL_LATE_PRODUCT_REPORT)#(group == config.Groups.EM))
    else:
        if month.is_current_month:
            report = ReportingBreakdown(base_facilities)
        else:
            report = ReportingBreakdown(base_facilities, month.datespan)

    return render_to_response("malawi/dashboard.html",
                              {"reporting_data": report,
                               "hsas_table": MalawiContactTable(Contact.objects.filter(is_active=True,
                                                                                       role__code="hsa"), request=request),
                               "graph_width": 200,
                               "graph_height": 200,
                               "month_pager": month,
                               "districts": get_districts().order_by("code"),
                               "location": request.location},
                               
                              context_instance=RequestContext(request))

@cache_page(60 * 15)
@place_in_request()
@vary_on_cookie
def hsas(request):
    hsas = hsas_below(request.location)
    districts = get_districts().order_by("id")
    facilities = get_facilities().order_by("parent_id")
    
    hsa_table = HSATable(hsas, request=request)
    return render_to_response("malawi/hsas.html",
        {
            "hsas": hsas,
            "hsa_table": hsa_table,
            "location": request.location,
            "districts": districts,
            "facilities": facilities
        }, context_instance=RequestContext(request)
    )
    
def hsa(request, code):
    if Contact.objects.filter(supply_point__code=code, is_active=True).count():
        hsa = get_object_or_404(Contact, supply_point__code=code, is_active=True)
    elif Contact.objects.filter(supply_point__code=code).count():
        hsa = Contact.objects.filter(supply_point__code=code)[0]
    else:
        raise Http404("Contact not found!")
    assert(hsa.supply_point.type.code == config.SupplyPointCodes.HSA)
    
    transactions = StockTransaction.objects.filter(supply_point=hsa.supply_point)
    chart_data = stocklevel_plot(transactions) 
    
    stockrequest_table = StockRequestTable(hsa.supply_point.stockrequest_set\
                                           .exclude(status=StockRequestStatus.CANCELED), request)
    return render_to_response("malawi/single_hsa.html",
        {
            "hsa": hsa,
            "id_str": "%s %s" % (hsa.supply_point.code[-2:], hsa.supply_point.code[:-2]),
            "chart_data": chart_data,
            "stockrequest_table": stockrequest_table
        }, context_instance=RequestContext(request)
    )

def deactivate_hsa(request, pk):
    hsa = get_object_or_404(Contact, pk=pk)
    hsa.is_active = False
    hsa.save()
    if hsa.supply_point and \
       hsa.supply_point.type == config.hsa_supply_point_type():
        hsa.supply_point.active = False
        hsa.supply_point.save()
        if hsa.supply_point.location:
            hsa.supply_point.location.is_active = False
            hsa.supply_point.location.save()

    messages.success(request, "HSA %(name)s deactivated." % {
        "name": hsa.name,
    })
    return redirect('malawi_hsa', code=hsa.supply_point.code)

def reactivate_hsa(request, code, name):
    hsa = get_object_or_404(Contact, supply_point__code=code, name=name)
    hsa.is_active = True
    hsa.save()
    if hsa.supply_point and \
       hsa.supply_point.type == config.hsa_supply_point_type():
        hsa.supply_point.active = True
        hsa.supply_point.save()
        if hsa.supply_point.location:
            hsa.supply_point.location.is_active = True
            hsa.supply_point.location.save()
    messages.success(request, "HSA %(name)s reactivated." % {
        "name": hsa.name,
    })
    return redirect('malawi_hsa', code=hsa.supply_point.code)

@cache_page(60 * 15)
@place_in_request()
@vary_on_cookie
def facilities(request):
    facilities = get_facilities().order_by("parent_id", "code")
    consumption_table = None
    if request.location:
        if request.location.type.slug == "district":
            table = None # nothing to do, handled by aggregate
            sps = hsa_supply_points_below(request.location)
            products = Product.objects.all()
            consumption_table = ConsumptionDataTable(object_list=[ConsumptionData(p, sps) for p in products], request=request)

        else:
            assert(request.location.type.slug == "facility")
            return HttpResponseRedirect(reverse("malawi_facility", args=[request.location.code]))
    else:
        table = DistrictTable(get_districts(), request=request)


    return render_to_response("malawi/facilities.html",
        {
            "location": request.location,
            "facilities": facilities,
            "table": table,
            "districts": get_districts().order_by("code"),
            "consumption_table": consumption_table
        }, context_instance=RequestContext(request))

@cache_page(60 * 15)
@filter_context
@datespan_in_request()
def facility(request, code, context={}):
    facility = get_object_or_404(SupplyPoint, code=code)
    assert(facility.type.code == config.SupplyPointCodes.FACILITY)
    em = group_for_location(facility.location) == config.Groups.EM
    mp = MonthPager(request)
    context["location"] = facility.location
    facility.location.supervisors = facility.contact_set.filter\
        (is_active=True, role__code=config.Roles.HSA_SUPERVISOR)
    facility.location.in_charges = facility.contact_set.filter\
        (is_active=True, role__code=config.Roles.IN_CHARGE)
    if em:
        context["stockrequest_table"] = HSAStockRequestTable\
            (StockRequest.objects.filter(supply_point__supplied_by=facility,
                                         requested_on__gte=mp.datespan.computed_startdate,
                                         requested_on__lte=mp.datespan.computed_enddate)\
                                 .exclude(status=StockRequestStatus.CANCELED), request)
    else:
        context["stockrequest_table"] = HSAStockRequestTable\
            (StockRequest.objects.filter(supply_point__supplied_by=facility,
                                         requested_on__gte=request.datespan.computed_startdate,
                                         requested_on__lte=request.datespan.computed_enddate)\
                                 .exclude(status=StockRequestStatus.CANCELED), request)
    context["em"] = em
    context["trueval"] = True # We've been reduced to this. http://stackoverflow.com/questions/3259279/django-templates
    context["month_pager"] = mp
    
    return render_to_response("malawi/single_facility.html",

        context, context_instance=RequestContext(request))
    
@permission_required_with_403("auth.admin_read")
def monitoring(request):
    reports = (ReportDefinition(slug) for slug in REPORT_SLUGS) 
    return render_to_response("malawi/monitoring_home.html", {"reports": reports},
                              context_instance=RequestContext(request))
@cache_page(60 * 15)
@permission_required_with_403("auth.admin_read")
@datespan_in_request()
def monitoring_report(request, report_slug):
    report_def = ReportDefinition(report_slug)
    if report_slug in REPORTS_CURRENT: request.datespan = "current"
    if report_slug in REPORTS_LOCATION:
        request.select_location=True
        code = request.GET.get("place", None)
        if code:
            request.location = Location.objects.get(code=code)
        else:
            request.location = None
        location = request.location
        instance = ReportInstance(report_def, request.datespan, request.location)
        facilities = get_facilities().order_by("parent_id", "code")
    else:
        instance = ReportInstance(report_def, request.datespan)
        facilities = None
        location = None
    return render_to_response("malawi/monitoring_report.html",
                              {"report": instance,
                               "facilities": facilities,
                               "location": location},
                              context_instance=RequestContext(request))

def monitoring_report_ajax(): pass

@permission_required("auth.admin_read")
def status(request):
    #TODO Put these settings in localsettings, probably
    f = urlopen(settings.KANNEL_URL)
    r = f.read()
    with open(settings.CELERY_HEARTBEAT_FILE) as f:
        r = "%s\n\nLast Celery Heartbeat:%s" % (r, f.read())
        
    return render_to_response("malawi/status.html", {'status': r}, context_instance=RequestContext(request))

@permission_required("auth.admin_read")
def airtel_numbers(request):
    airtelcontacts = Contact.objects.select_related().filter(connection__backend__name='airtel-smpp')
    users = []
    for a in airtelcontacts:
        d = {
            'name': a.name,
            'phone': a.phone,
            'registered': a.message_set.all().order_by('-date')[0].date
        }
        users.append(d)
    users.sort(cmp=_sort_date, reverse=True)
    return render_to_response("malawi/airtel.html", {'users':users}, context_instance=RequestContext(request))

@csrf_exempt
def scmgr_receiver(request):
    if request.method != 'POST':
        return HttpResponse("You must submit POST data to this url.")
    data = request.POST.get('data', None)
    result = json.simplejson.loads(data)
    processed = 0
    for r in result:
        try:
            facility = SupplyPoint.objects.get(code=HEALTH_FACILITY_MAP[r[3]])
            pc = PRODUCT_CODE_MAP[r[6]].lower()
            product = Product.objects.get(sms_code=pc)
            date = datetime(year=r[4][0],month=r[4][1], day=1)
            if ProductReport.objects.filter(supply_point=facility, product=product, report_date=date).exists():
                # Server sent us some data we already have.  This means they should stop sending it.
                return HttpResponse('cStock SCMgr data fully updated.')
            quantity = r[0]
            is_stocked_out = r[2]
            if not quantity and not is_stocked_out:
                # If stock quantity is 0, but stockout not indicated, this line wasn't filled in.
                continue
            facility.report_stock(product, quantity, date=date)
            logging.info("SCMgr: Processed stock report %s %s %s %s" % (facility,product,quantity,date))
            processed += 1
        except (KeyError, SupplyPoint.DoesNotExist, Product.DoesNotExist) as e:
            # Server sent us some data we don't care about.  Keep on truckin'.
            continue
    if result:
        ret = "Processed %d entries." % processed
        return HttpResponse(ret, status=201) # Keep sending us stuff if you have more to send.
    else:
        ret = "Got no data -- ending update."
        return HttpResponse(ret)

def verify_ajax(request):
    field = request.GET.get('field', None)
    val = request.GET.get('val', None)
    if not (field and val): return json.dump(False)
    if field == 'facility_code':
        if SupplyPoint.objects.filter(type__code='hf', code=val).exists():
            return json.dump(True)

@datespan_in_request()
def export_amc_csv(request):
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=amc.csv'
    writer = UnicodeWriter(response)
    _, data_rows = amc_plot(SupplyPoint.objects.filter(active=True), request.datespan)
    datetimes = [datetime(m, y, 1) for m, y in request.datespan.months_iterator()]
    products = Product.objects.order_by('sms_code')
    row = ['Year', 'Month']
    row.extend([p.sms_code for p in products])
    writer.writerow(row)
    for dt in datetimes:
        row = [dt.year, dt.month]
        v = data_rows[dt]
        for p in products:
            row.append(v[p.sms_code])
        writer.writerow(row)
    return response

def _sort_date(x,y):
    if x['registered'] < y['registered']: return -1
    if x['registered'] > y['registered']: return 1
    return 0

class MonthPager(object):
    """
    Utility class to show a month pager, e.g. << August 2011 >>
    """
    def __init__(self, request):
        self.month = int(request.GET.get('month', datetime.utcnow().month))
        self.year = int(request.GET.get('year', datetime.utcnow().year))
        self.begin_date = datetime(year=self.year, month=self.month, day=1)
        self.end_date = (self.begin_date + timedelta(days=32)).replace(day=1) - timedelta(seconds=1) # last second of previous month
        self.prev_month = self.begin_date - timedelta(days=1)
        self.next_month = self.end_date + timedelta(days=1)
        self.show_next = self.end_date < datetime.utcnow().replace(day=1)
        self.is_current_month = (self.month == datetime.utcnow().month and self.year == datetime.utcnow().year)
        self.datespan = DateSpan(self.begin_date, self.end_date)

    