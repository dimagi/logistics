from datetime import datetime
from urllib2 import urlopen
from collections import defaultdict
import json

from django.conf import settings
from django.contrib import messages
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import permission_required, user_passes_test
from django.contrib.auth.models import User as auth_user
from django.contrib.auth.models import Group as auth_group
from django.db.models.aggregates import Count

from logistics_project.utils.csv import UnicodeWriter
from logistics_project.utils.dates import months_between, add_months
from logistics_project.utils.decorators.datespan import datespan_in_request

from rapidsms.models import Contact
from rapidsms.contrib.locations.models import Location
from rapidsms.models import Backend, Connection
from rapidsms.contrib.messagelog.models import Message

from logistics.models import SupplyPoint, Product, LogisticsProfile,\
    StockTransaction, StockRequestStatus, StockRequest, ProductReport, ContactRole
from logistics.decorators import place_in_request
from logistics.charts import stocklevel_plot
from logistics.util import config
from logistics.charts import amc_plot

from logistics_project.apps.malawi.warehouse.report_utils import datespan_default
from logistics_project.apps.malawi.exceptions import IdFormatException
from logistics_project.apps.malawi.tables import HSATable, StockRequestTable
from logistics_project.apps.malawi.util import get_districts, get_facilities, hsas_below, format_id, \
    deactivate_product, get_managed_products_for_contact, get_or_create_user_profile
from logistics_project.apps.malawi.reports import ReportInstance, ReportDefinition,\
    REPORT_SLUGS, REPORTS_CURRENT, REPORTS_LOCATION
from logistics_project.apps.malawi.models import Organization
from logistics_project.apps.malawi.forms import OrganizationForm, LogisticsProfileForm,\
    UploadFacilityFileForm, ProductForm, UserForm

from logistics_project.apps.malawi.loader import (get_facility_export,
    FacilityLoaderValidationError, FacilityLoader)
from django.views.decorators.http import require_POST
from logistics_project.apps.outreach.models import OutreachMessage, OutreachQuota
from django.db.models.query_utils import Q
from rapidsms.contrib.messaging.utils import send_message
from logistics_project.apps.malawi.templatetags.malawi_warehouse_tags import is_district_user


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
        table["data"].append({"url": reverse("malawi_edit_organization", kwargs={'pk': org.id}),
            "data": [org.name, org.contact_set.all().count(),
                " ".join([s.name for s in org.managed_supply_points.all()])]})

    table["height"] = min(480, (orgs.count()+1)*30)

    context = {
        "orgs": orgs,
        "table": table,
    }
    return render_to_response("%s/organizations.html" % settings.MANAGEMENT_FOLDER, context)

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
    })
    
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
    })

@cache_page(60 * 15)
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
            " ".join([com.sms_code for com in get_managed_products_for_contact(c)]),
            c.organization.name if c.organization else ""]})

    table["height"] = min(480, (contacts.count()+1)*30)

    context = {
        "contacts": contacts,
        "table": table,
    }
    return render_to_response("%s/contacts.html" % settings.MANAGEMENT_FOLDER, context)


def permissions(request):
    users = auth_user.objects.all()
    groups = auth_group.objects.all()
    table = {
        "id": "user-table",
        "is_datatable": True,
        "is_downloadable": False,
        "header": ["User", "District", "Organization", "Groups"],
        "data": [],
    }
    for u in users:
        prof = get_or_create_user_profile(u)
        table["data"].append({"url": reverse("malawi_edit_permissions", kwargs={'pk': prof.id}), 
            "data": [u.username, prof.supply_point,
                prof.organization.name if prof.organization else "",
                " ".join([g.name for g in u.groups.all()])]})

    table["height"] = min(480, (users.count()+1)*30)

    context = {
        "users": users,
        "groups": groups,
        "table": table,
    }
    return render_to_response("%s/permissions.html" % settings.MANAGEMENT_FOLDER, context)


def edit_permission(request, pk):
    prof = get_object_or_404(LogisticsProfile, pk=pk)
    if request.method == 'POST':
        form = LogisticsProfileForm(request.POST, instance=prof) 
        if form.is_valid(): 
            prof = form.save()
            messages.success(request, "Permissions for '%s' were successfully saved"  % prof.user.username)
            return HttpResponseRedirect(reverse('malawi_permissions'))

    form = LogisticsProfileForm(instance=prof) 

    context = { 'user': prof.user.username,
                'form': form,
              }

    return render_to_response("%s/edit_permission.html" % settings.MANAGEMENT_FOLDER, context)


def create_account(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'User "{0}" was created. Set permissions here.'.format(user.username))
            prof = get_or_create_user_profile(user)
            return HttpResponseRedirect(reverse('malawi_edit_permissions', args=[prof.pk]))
    else:
        form = UserForm()
    return render_to_response("%s/add_user_account.html" % settings.MANAGEMENT_FOLDER,
                              {'form': form})


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
        try:
            sp = SupplyPoint.objects.get(location=loc)
        except SupplyPoint.DoesNotExist:
            # if for whatever reason this isn't found don't fail hard.
            continue
        table["data"].append([loc.name, loc.code,
            loc.type.name if loc.type else "",
            sp.supplied_by.name if sp.supplied_by else ""])

    table["height"] = min(480, (locs.count()+1)*30)

    context = {
        "locs": locs,
        "table": table,
    }
    return render_to_response("%s/places.html" % settings.MANAGEMENT_FOLDER, context)



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
    def _fmt_name(product):
        return '<a href="{url}">{name}</a>'.format(
            url=reverse('malawi_single_product', args=[str(product.pk)]),
            name=product.name,
        )

    for prd in prds:
        table["data"].append([_fmt_name(prd), prd.sms_code, prd.average_monthly_consumption,
            prd.emergency_order_level, prd.type.name if prd.type else ""])

    table["height"] = min(480, (prds.count()+1)*30)

    context = {
        "prds": prds,
        "table": table,
    }
    return render_to_response("%s/products.html" % settings.MANAGEMENT_FOLDER, context)


def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            p = form.save()
            messages.success(request, 'Product "{0}" was created.'.format(p.name))
            return HttpResponseRedirect(reverse('malawi_products'))
    else:
        form = ProductForm()
    return render_to_response("%s/add_product.html" % settings.MANAGEMENT_FOLDER,
                              {'form': form})


def single_product(request, pk):
    p = get_object_or_404(Product, pk=pk)
    return render_to_response("%s/single_product.html" % settings.MANAGEMENT_FOLDER,
                              {'product': p})


def deactivate_product_view(request, pk):
    p = get_object_or_404(Product, pk=pk)
    if request.method=="POST":
        deactivate_product(p)
        messages.success(request, "%s was successfully deactivated" % p.name)
        return HttpResponseRedirect(reverse('malawi_products'))
    return render_to_response("%s/deactivate_product.html" % settings.MANAGEMENT_FOLDER,
                              {'product': p})


def help(request):
    return render_to_response("malawi/help.html")


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
        }
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
        }
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


@permission_required("auth.admin_read")
def monitoring(request):
    reports = (ReportDefinition(slug) for slug in REPORT_SLUGS) 
    return render_to_response("malawi/monitoring_home.html", {"reports": reports})


@cache_page(60 * 15)
@permission_required("auth.admin_read")
@datespan_default
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
                               "location": location})


@permission_required("auth.admin_read")
def status(request):
    f = urlopen(settings.KANNEL_URL)
    r = f.read()
    with open(settings.CELERY_HEARTBEAT_FILE) as f:
        r = "%s\n\nLast Celery Heartbeat:%s" % (r, f.read())
        
    return render_to_response("malawi/status.html", {'status': r})


def is_kannel_up(request):
    try:
        f = urlopen(settings.KANNEL_URL)
        r = f.read()
        if 'online' in r:
            return HttpResponse('kannel is up', status=200)
    except Exception:
        pass
    return HttpResponse('kannel is down', status=500)


@permission_required("auth.admin_read")
def airtel_numbers(request):
    airtelcontacts = Contact.objects.select_related().filter(connection__backend__name=config.AIRTEL_BACKEND_NAME)
    users = []
    for a in airtelcontacts:
        d = {
            'name': a.name,
            'phone': a.phone,
            'registered': a.message_set.all().order_by('-date')[0].date
        }
        users.append(d)
    users.sort(cmp=_sort_date, reverse=True)
    return render_to_response("malawi/airtel.html", {'users':users})


def verify_ajax(request):
    field = request.GET.get('field', None)
    val = request.GET.get('val', None)
    if not (field and val): return json.dump(False)
    if field == 'facility_code':
        if SupplyPoint.objects.filter(type__code='hf', code=val).exists():
            return json.dump(True)


def manage_hsas(request):
    hsas = SupplyPoint.objects.filter(active=True, type__code=config.SupplyPointCodes.HSA).select_related(
        'supplied_by'
    )
    table = {
        "id": "loc-table",
        "is_datatable": True,
        "is_downloadable": False,
        "header": ["Name", "Code", "Facility"],
        "data": [],
    }
    for hsa in hsas:
        table["data"].append([
            '<a href="{0}" target="_blank">{1}</a>'.format(
                reverse('malawi_manage_hsa', args=[hsa.pk]),
                hsa.name,
            ),
            hsa.code,
            hsa.supplied_by.name,
        ])

    table["height"] = min(480, (hsas.count()+1)*30)

    context = {
        "table": table,
    }
    return render_to_response("%s/hsas.html" % settings.MANAGEMENT_FOLDER, context)


def manage_hsa(request, pk):
    hsa = get_object_or_404(SupplyPoint, pk=pk)
    phone_numbers = [c.default_connection.identity for c in hsa.contact_set.all()]
    return render_to_response(
        "%s/hsa.html" % settings.MANAGEMENT_FOLDER,
        {
            'hsa': hsa,
            'phone_numbers': '<br>'.join(phone_numbers) if phone_numbers else '-',
        },
    )


@require_POST
def deactivate_hsa(request, pk):
    hsa = get_object_or_404(SupplyPoint, pk=pk)
    assert hsa.type == config.hsa_supply_point_type()
    hsa.active = False
    hsa.save()
    hsa.location.is_active = False
    hsa.location.save()
    deactivated_numbers = []
    for contact in hsa.contact_set.filter(is_active=True):
        contact.is_active = False
        deactivated_numbers.append(contact.default_connection.identity)
        contact.save()

    notice = "Successfully deactivated {0}".format(hsa)
    if deactivated_numbers:
        notice = '{0}{1}'.format(notice,
                                 ' with the following phone number(s):{0}'.format(', '.join(deactivated_numbers)))
    messages.success(request, notice)
    return HttpResponseRedirect(reverse('malawi_manage_hsas'))


def manage_facilities(request):
    form = UploadFacilityFileForm()
    return render_to_response("malawi/manage_facilities.html", 
        {'form': form})


def download_facilities(request):
    response = HttpResponse()
    response['Content-Disposition'] = 'attachment; filename=cstock-facilities.csv'
    get_facility_export(response)
    return response


@require_POST
def upload_facilities(request):
    form = UploadFacilityFileForm(request.POST, request.FILES)
    if form.is_valid():
        f = request.FILES['file']
        try: 
            count = FacilityLoader(f).run()
            messages.info(request, "Successfully processed %s rows." % count)
        except FacilityLoaderValidationError as f:
            messages.error(request, f.validation_msg)
        except Exception as e:
            messages.error(request, "Something went wrong with that upload. " 
                           "Please double check the file format or "
                           "try downloading a new copy. Your error message "
                           "is: %s" % e)
    else:
        messages.error(request, "Please select a file")    
    return HttpResponseRedirect(reverse("malawi_manage_facilities"))

@user_passes_test(is_district_user)
def outreach(request):
    contacts = []
    if request.GET.get('q'):
        search = request.GET['q']
        contacts = Contact.objects.filter(
            Q(name__icontains=search) | Q(connection__identity__icontains=search)
        )

    sent = OutreachMessage.sent_this_month(request.user)
    allowed = OutreachQuota.get_quota(request.user)
    remaining = OutreachQuota.get_remaining(request.user)
    return render_to_response("malawi/outreach.html",
        {
            'sent': sent,
            'remaining': remaining,
            'allowed': allowed,
            'contacts': contacts,
         },
    )

@require_POST
@user_passes_test(is_district_user)
def send_outreach(req):
    text = req.POST["text"]
    data = json.loads(req.POST["recipients"])
    to_send = len(data)
    remaining = OutreachQuota.get_remaining(req.user)
    resp = {}
    if to_send > remaining:
        resp = {
            'status': 'error',
            'msg': ('Sorry that would exceed your quota for the month '
                    '({rem} messages remaining).').format(
                        amt=to_send, rem=remaining),
            'remaining': remaining,
        }
    else:
        sent_to = []
        for item in data:
            contact = get_object_or_404(Contact, pk=item)
            send_message(contact.default_connection, text)
            sent_to.append(contact)
            OutreachMessage.objects.create(sent_by=req.user)
        resp = {
            'status': 'success',
            'msg': '%s sent to %s' % (text, ', '.join(str(c) for c in sent_to)),
            'remaining': OutreachQuota.get_remaining(req.user),
        }
    return HttpResponse(json.dumps(resp), content_type='application/json')

    
@datespan_in_request()
def export_amc_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=amc.csv'
    products = Product.objects.filter(type__base_level=config.BaseLevel.HSA).order_by('sms_code')
    writer = UnicodeWriter(response)
    _, data_rows = amc_plot(
        SupplyPoint.objects.filter(active=True, type__code=config.SupplyPointCodes.HSA),
        request.datespan,
        products=products
    )
    datetimes = [datetime(m, y, 1) for m, y in request.datespan.months_iterator()]
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


@permission_required("is_superuser")
def register_user(request, template="malawi/register-user.html"):
    context = dict()
    context['facilities'] = SupplyPoint.objects.filter(type__code="hf").order_by('code')
    context['backends'] = Backend.objects.all()
    context['dialing_code'] = settings.COUNTRY_DIALLING_CODE # [sic]
    if request.method != 'POST':
        return render_to_response(template, context)

    id = request.POST.get("id", None)
    facility = request.POST.get("facility", None)
    name = request.POST.get("name", None)
    number = request.POST.get("number", None)
    backend = request.POST.get("backend", None)

    if not (id and facility and name and number and backend):
        messages.error(request, "All fields must be filled in.")
        return render_to_response(template, context)
    hsa_id = None
    try:
        hsa_id = format_id(facility, id)
    except IdFormatException:
        messages.error(request, "HSA ID must be a number between 0 and 99.")
        return render_to_response(template, context)

    try:
        parent = SupplyPoint.objects.get(code=facility)
    except SupplyPoint.DoesNotExist:
        messages.error(request, "No facility with that ID.")
        return render_to_response(template, context)

    if Location.objects.filter(code=hsa_id).exists():
        messages.error(request, "HSA with that code already exists.")
        return render_to_response(template, context)

    try:
        number = int(number)
    except ValueError:
        messages.error(request, "Phone number must contain only numbers.")
        return render_to_response(template, context)

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

    return render_to_response(template, context)


@datespan_default
def sms_tracking(request):
    
    class ContactCache(object):
        def __init__(self):
            self.contacts = {}
        
        def get(self, pk):
            return self.contacts[pk] if pk in self.contacts else Contact.objects.get(pk=pk)
    
    orgs = dict(zip(Organization.objects.all(), 
                    [defaultdict(lambda x: 0) for i in range(Organization.objects.count())]))
    # if I was smarter I'd figure out a way to do this query with django aggregates,
    # but for now we'll just do it all in memory
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
    
    return render_to_response("malawi/new/management/sms-tracking.html",
                              {"organizations": orgs})


@datespan_default
def telco_tracking(request):
    results = []

    for year, month in months_between(request.datespan.computed_startdate,
                                      request.datespan.computed_enddate):
        period_start = datetime(year, month, 1)
        endyear, endmonth = add_months(year, month, 1)
        period_end = datetime(endyear, endmonth, 1)
        tnm_msgs = Message.objects.filter(connection__backend__name='tnm-smpp',
                                          date__gte=period_start,
                                          date__lt=period_end)
        airtel_msgs = Message.objects.filter(connection__backend__name='airtel-smpp',
                                             date__gte=period_start,
                                             date__lt=period_end)
        results.append((period_start.strftime("%B, %Y"),
                        tnm_msgs.filter(direction="I").count(),
                        tnm_msgs.filter(direction="O").count(),
                        tnm_msgs.count(),
                        airtel_msgs.filter(direction="I").count(),
                        airtel_msgs.filter(direction="O").count(),
                        airtel_msgs.count()))

    return render_to_response("malawi/new/management/telco-tracking.html",
                              {"results": results})


def set_current_dashboard(request):
    base_level = request.GET.get('base_level')
    profile = get_or_create_user_profile(request.user)
    if base_level == config.BaseLevel.HSA and profile.can_view_hsa_level_data:
        profile.current_dashboard_base_level = config.BaseLevel.HSA
        profile.save()
    elif base_level == config.BaseLevel.FACILITY and profile.can_view_facility_level_data:
        profile.current_dashboard_base_level = config.BaseLevel.FACILITY
        profile.save()
    else:
        raise Http404()

    return HttpResponseRedirect(reverse('malawi_dashboard'))


def raise_500(request):
    raise Exception('This is a simulated error from cstock.')
