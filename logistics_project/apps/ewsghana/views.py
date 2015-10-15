#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

import re
from django.contrib.auth.models import User
from django.contrib.auth.decorators import permission_required, \
    login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.comments.models import Comment
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template.context import RequestContext
from django_tablib import ModelDataset
from django_tablib.base import mimetype_map
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt
from dimagi.utils import csv 
from dimagi.utils.dates import DateSpan
from dimagi.utils.decorators.datespan import datespan_in_request
from rapidsms.models import Contact
from rapidsms.contrib.messagelog.models import Message
from rapidsms.contrib.locations.models import Location
from rapidsms.conf import settings
from auditcare.views import auditAll
from auditcare.models import AccessAudit
from registration.views import register as django_register
from email_reports.views import email_reports as logistics_email_reports
from email_reports.decorators import magic_token_required
from logistics.decorators import place_in_request
from logistics.models import Product, SupplyPoint, LogisticsProfile, ProductStock, StockTransaction
from logistics.reports import ReportingBreakdown, TotalStockByLocation
from logistics.tables import FacilityTable
from logistics.view_decorators import geography_context
from logistics.views import LogisticsMessageLogView
from logistics.views import reporting as logistics_reporting
from logistics.views import facilities_by_products as logistics_facilities_by_products
from logistics.views import district_dashboard, aggregate, stockonhand_facility
from logistics.view_decorators import filter_context
from logistics.util import config
from logistics_project.apps.web_registration.views import admin_does_all
from logistics_project.apps.ewsghana.tables import FacilityDetailTable, \
    LocationTable, CommentTable
from logistics_project.apps.ewsghana.models import GhanaFacility
from logistics_project.apps.ewsghana.forms import EWSGhanaSMSRegistrationForm, \
    LocationForm
from logistics_project.apps.ewsghana.permissions import FACILITY_MANAGER_GROUP_NAME
from .forms import FacilityForm, EWSGhanaBasicWebRegistrationForm, \
    EWSGhanaManagerWebRegistrationForm, EWSGhanaAdminWebRegistrationForm
from logistics_project.apps.registration.views import registration as logistics_registration
from .forms import FacilityForm
from .tables import AuditLogTable, EWSMessageTable

""" Usage-Related Views """
@geography_context
@place_in_request()
def reporting(request, context={}, template="ewsghana/reporting.html"):
    return logistics_reporting(request=request,  
                               context=context, template=template, 
                               destination_url="ewsghana_reporting")

class EWSGhanaMessageLogView(LogisticsMessageLogView):
    def get_context(self, request, context):
        context = super(EWSGhanaMessageLogView, self).get_context(request, context)
        context["messages_table"] = EWSMessageTable(context['messages_qs'], request=request)
        return context
    
    def get(self, request, template="ewsghana/messagelog.html"):
        return super(EWSGhanaMessageLogView, self).get(request, template=template)

def help(request, template="ewsghana/help.html"):
    commodities = Product.objects.filter(is_active=True).order_by('name')
    return render_to_response(
        template, {'commodities':commodities}, 
        context_instance=RequestContext(request)
    )

@cache_page(60 * 15)
def export_messagelog(request, format='xls'):
    class MessageDataSet(ModelDataset):
        class Meta:
            # hack to limit the # of messages returns
            # so that we don't crash the server when the log gets too big
            # in the long term, should implement asynchronous processing + progress bar
            queryset = Message.objects.order_by('-date')[:10000]
    dataset = getattr(MessageDataSet(), format)
    response = HttpResponse(
        dataset,
        mimetype=mimetype_map.get(format, 'application/octet-stream')
        )
    response['Content-Disposition'] = 'attachment; filename=messagelog.xls'
    return response

def _prep_audit_for_display(auditevents):
    realEvents = []
    for a in auditevents:
        designation = organization = facility = location = first_name = last_name = ''
        try:
            user = User.objects.get(username=a.user)
        except User.DoesNotExist:
            # OK - anonymous user
            pass
        else:
            first_name = user.first_name
            last_name = user.last_name
            try:
                profile = user.get_profile()
            except LogisticsProfile.DoesNotExist:
                profile = None
            else:
                designation = profile.designation if profile.designation else '' 
                organization = profile.organization if profile.organization else ''
                facility = profile.supply_point if profile.supply_point else ''
                location = profile.location if profile.location else ''
        realEvents.append({'user': a.user, 
                           'date': a.event_date, 
                           'class': a.doc_type, 
                           'access_type': a.access_type, 
                           'first_name': first_name,
                           'last_name': last_name,
                           'designation': designation, 
                           'organization': organization, 
                           'facility': facility, 
                           'location': location })
    return realEvents

def auditor_export(request):
    """ consider using the async export_auditor task in stead of this view """
    auditEvents = AccessAudit.view("auditcare/by_date_access_events", 
                                   descending=True, include_docs=True).all()
    detailedEvents = _prep_audit_for_display(auditEvents)
    response = HttpResponse(mimetype=mimetype_map.get(format, 'application/octet-stream'))
    response['Content-Disposition'] = 'attachment; filename=webusage.xls'
    writer = csv.UnicodeWriter(response)
    writer.writerow(["Date ", "User", "Access_Type", "Designation", 
                     "Organization", "Facility", "Location", "First_Name", 
                     "Last_Name"])
    for e in detailedEvents:
        writer.writerow([e['date'], e['user'], e['class'], e['designation'],
                         e['organization'], e['facility'], e['location'], 
                         e['first_name'], e['last_name']])
    return response    

def auditor(request, template="ewsghana/auditor.html"):
    """
    NOTE: this truncates the log by default to the last 750 entries
    To get the complete usage log, web users should export to excel 
    This does a wildly inefficient couch<->postgres join. optimize later if need be.
    """
    MAX_ENTRIES = 500
    if request.method == "GET" and 'search' in request.GET:
            search = request.GET['search']
            matches = AccessAudit.get_db().search("auditcare/search", 
                                                  handler="_fti/_design",
                                                  q=search, 
                                                  include_docs=True)
            auditEvents = [AccessAudit.wrap(res["doc"]) for res in matches]
    else:
            auditEvents = AccessAudit.view("auditcare/by_date_access_events", 
                                   limit=MAX_ENTRIES, 
                                   descending=True, include_docs=True).all()
    detailedEvents = _prep_audit_for_display(auditEvents)
    return render_to_response(template, 
                              {"audit_table": AuditLogTable(detailedEvents, request=request)}, 
                              context_instance=RequestContext(request))

def register_web_user(request, pk=None, 
                   template='web_registration/admin_registration.html', 
                   success_url='admin_web_registration_complete'):
    if request.user.is_superuser:
        Form = EWSGhanaAdminWebRegistrationForm
    elif request.user.groups.filter(name=FACILITY_MANAGER_GROUP_NAME).exists():
        Form = EWSGhanaManagerWebRegistrationForm
    else:
        Form = EWSGhanaBasicWebRegistrationForm
    return admin_does_all(request, pk, Form, 
                          template=template, 
                          success_url=success_url)

""" Configuration-Related Views """
def web_registration(request, template_name="registration/registration_form.html"):
    return django_register(request)

def email_reports(request, pk=None, context={}, template="ewsghana/email_reports.html"):
    return logistics_email_reports(request, pk, context, template)

@place_in_request()
def facilities_list(request, context={}, template="ewsghana/facilities_list.html"):
    if request.location is None:
        request.location = get_object_or_404(Location, code=settings.COUNTRY)
    facilities = request.location.all_facilities()
    context ['table'] = FacilityDetailTable(facilities, request=request)
    context['destination_url'] = "facilities_list"
    context['location'] = request.location
    return render_to_response(
        template, context, context_instance=RequestContext(request)
    )

def facility_detail(request, code, context={}, template="ewsghana/single_facility.html"):
    facility = get_object_or_404(GhanaFacility, code=code)
    context ['facility'] = facility
    return render_to_response(
        template, context, context_instance=RequestContext(request)
    )

""" Customized Views """

@permission_required('logistics.add_supplypoint')
@transaction.commit_on_success
@place_in_request()
def facility(req, pk=None, template="ewsghana/facilityconfig.html"):
    facility = None
    form = None
    incharges = None
    sms_users = None
    klass = "Facility"
    if pk is not None:
        facility = get_object_or_404(
            GhanaFacility, pk=pk)
        incharges = facility.incharges()
        sms_users = Contact.objects.filter(is_active=True, supply_point=facility)
    if req.method == "POST":
        if req.POST["submit"] == "Delete %s" % klass:
            facility.deactivate()
            return HttpResponseRedirect(
                "%s?deleted=%s" % (reverse('facility_view'), 
                                   unicode(facility)))
        else:
            form = FacilityForm(instance=facility,
                                data=req.POST)
            if form.is_valid():
                facility = form.save()
                if pk is not None:
                    url = "%s?updated=%s"
                else:
                    url = "%s?created=%s"
                return HttpResponseRedirect(
                    url % (reverse('facility_edit', kwargs={'pk':facility.pk}), 
                                       unicode(facility)))
    else:
        form = FacilityForm(instance=facility)
    products = Product.objects.filter(is_active=True).order_by('name')
    created = None
    deleted = None
    search = None
    facilities = GhanaFacility.objects.filter(active=True)
    if req.method == "GET":
        if "created" in req.GET:
            created = req.GET['created']
        elif "deleted" in req.GET:
            deleted = req.GET['deleted']
        if 'search' in req.GET:
            search = req.GET['search']
            safe_search = re.escape(search)
            facilities = facilities.filter(Q(name__iregex=safe_search) |\
                                           Q(location__name__iregex=safe_search))
    if 'search' not in req.GET and req.location and \
      req.location.code != settings.COUNTRY: 
        facilities = req.location.all_facilities()
    return render_to_response(
        template, {
            "search_enabled": True, 
            "search": search, 
            "created": created, 
            "deleted": deleted, 
            "sms_users": sms_users, 
            "incharges": incharges,
            "table": FacilityTable(facilities, request=req),
            "form": form,
            "object": facility,
            "klass": klass,
            "klass_view": reverse('facility_view'), 
            "products": products, 
            "location": req.location, 
            "destination_url": "facility_view"
        }, context_instance=RequestContext(req)
    )

@user_passes_test(lambda u: u.is_superuser)
@transaction.commit_on_success
def district(req, code=None, template="logistics/config.html"):
    district = None
    form = None
    klass = "District"
    if code is not None:
        district = get_object_or_404(
            Location, code=code)
    if req.method == "POST":
        if req.POST["submit"] == "Delete %s" % klass:
            district.deactivate()
            return HttpResponseRedirect(
                "%s?deleted=%s" % (reverse('district_view'), 
                                   unicode(district)))
        else:
            form = LocationForm(instance=district,
                                data=req.POST)
            if form.is_valid():
                district = form.save()
                if district:
                    url = "%s?updated=%s"
                else:
                    url = "%s?created=%s"
                return HttpResponseRedirect(
                    url % (reverse('district_view'), 
                           unicode(district)))
    else:
        form = LocationForm(instance=district)
    created = None
    deleted = None
    search = None
    districts = Location.objects.filter(type__slug=config.LocationCodes.DISTRICT, 
                                        is_active=True)
    if req.method == "GET":
        if "created" in req.GET:
            created = req.GET['created']
        elif "deleted" in req.GET:
            deleted = req.GET['deleted']
        if 'search' in req.GET:
            search = req.GET['search']
            safe_search = re.escape(search)
            districts = districts.filter(name__iregex=safe_search)
    return render_to_response(
        template, {
            "search_enabled": True, 
            "search": search, 
            "created": created, 
            "deleted": deleted, 
            "table": LocationTable(districts, request=req),
            "form": form,
            "object": district,
            "klass": klass,
            "klass_view": reverse('district_view'), 
        }, context_instance=RequestContext(req)
    )

@staff_member_required
@transaction.commit_on_success
def activate_district(request, code):
    district = get_object_or_404(Location, code=code)
    district.activate()
    return HttpResponse("success")

@transaction.commit_on_success
def my_web_registration(request, 
                        template='web_registration/admin_registration.html', 
                        success_url='admin_web_registration_complete'):
    context = {}
    context['hide_delete'] = True
    Form = EWSGhanaBasicWebRegistrationForm
    return admin_does_all(request, request.user.pk, Form, context, template, success_url)

def sms_registration(request, *args, **kwargs):
    context = {}
    context['destination_url'] = "ewsghana_sms_registration"
    kwargs['contact_form'] = EWSGhanaSMSRegistrationForm
    ret = logistics_registration(request, *args, context=context, **kwargs)
    return ret

def configure_incharge(request, sp_code, template="ewsghana/config_incharge.html"):
    klass = "Facility"
    facility = get_object_or_404(GhanaFacility, code=sp_code)
    if request.method == "POST":
        if request.POST["submit"] == "Save In-Charge":
            if "incharge_pk" in request.POST and request.POST["incharge_pk"]:
                incharge = Contact.objects.get(pk=int(request.POST["incharge_pk"]))
                if incharge in facility.reportees():
                    # if it's a supervisor @ this facility, then no need to add supervised_by
                    # just remove it
                    if facility.supervised_by is not None:
                        facility.supervised_by = None
                        facility.save()
                elif incharge.supply_point != facility.supervised_by:
                    facility.supervised_by = incharge.supply_point
            else:
                facility.supervised_by = None
            facility.save()
        return HttpResponseRedirect(
            reverse('facility_edit', kwargs={"pk":facility.pk}))
    form = FacilityForm(instance=facility)
    for key in form.fields.keys():
        form.fields[key].widget.attrs['disabled'] = True
        form.fields[key].widget.attrs['readonly'] = True
    return render_to_response(
        template, {
            "candidates": facility.get_district_incharges(), 
            "form": form,
            "object": facility,
            "klass": klass,
            "klass_view": reverse('facility_view')
        }, context_instance=RequestContext(request)
    )

@csrf_exempt
@geography_context
@filter_context
def dashboard(request, context={}):
    prof = None 
    try:
        if not request.user.is_anonymous():
            prof = request.user.get_profile()
    except LogisticsProfile.DoesNotExist:
        pass

    if prof:
        if prof.supply_point:
            return stockonhand_facility(request, prof.supply_point.code)
        elif prof.location:
            if prof.location.type.slug == config.LocationCodes.DISTRICT or \
              prof.location.type.slug == config.LocationCodes.REGION:
                return HttpResponseRedirect("%s?place=%s" % \
                                            (reverse("district_dashboard"),prof.location.code) ) 
            else:
                request.location = prof.location
                return HttpResponseRedirect("%s?place=%s" % (reverse("district_dashboard"), settings.DEFAULT_LOCATION) )
    return HttpResponseRedirect("%s?place=%s" % (reverse("district_dashboard"), settings.DEFAULT_LOCATION) )

def _get_medical_stores():
    return SupplyPoint.objects.filter(active=True,
                                      type__code__in=config.SupplyPointCodes.MEDICAL_STORES).\
                                      order_by('type', 'name')
                                      
def medical_stores(request, context={}, template="ewsghana/medical_stores.html"):
    context['stores'] = _get_medical_stores()
    return render_to_response(
        template, context, context_instance=RequestContext(request)
    )

@csrf_exempt
@cache_page(60 * 15)
@geography_context
@filter_context
@magic_token_required()
@datespan_in_request()
@place_in_request()
def facilities_by_products(request, context={}, template="ewsghana/facilities_by_products.html"):
    context['stores'] = _get_medical_stores()
    context['destination_url'] = "ewsghana_facilities_by_products"
    return logistics_facilities_by_products(request, context=context, 
                                            template=template)

def comments(request, context={}, template="ewsghana/comments.html"):
    context['site'] = Site.objects.all()[0]
    context ['comment_table'] = CommentTable(Comment.objects.all(), request=request)
    return render_to_response(
        template, context, context_instance=RequestContext(request)
    )

@cache_page(60 * 15)
@place_in_request()
def stock_at_medical_stores(request, context=None):
    """
    View for generating HTML email reports via email-reports submodule
    While this can be viewed on the web, primarily this is rendered using a fake
    request object so care should be taken accessing items on the request.
    However request.user will be set.
    """
    request.location = get_object_or_404(Location, code=settings.COUNTRY)
    context = context or {}
    facilities = _get_medical_stores()
    datespan = DateSpan.since(settings.LOGISTICS_DAYS_UNTIL_LATE_PRODUCT_REPORT)
    report = ReportingBreakdown(facilities, datespan, 
        days_for_late=settings.LOGISTICS_DAYS_UNTIL_LATE_PRODUCT_REPORT)
    products_by_location = TotalStockByLocation(facilities, datespan).products
    context.update({
        'location': request.location,
        'facilities': facilities,
        'facility_count': facilities.count(),
        'report': report,
        'product_stats': products_by_location,
    })
    return render_to_response("logistics/summary.html", context, context_instance=RequestContext(request))


def global_stats(request):
    active_sps = SupplyPoint.objects.filter(active=True)
    hsa_type = getattr(config.SupplyPointCodes, 'HSA', 'nomatch')
    country = Location.objects.filter(type__slug='country')
    region = Location.objects.filter(type__slug='region')
    district = Location.objects.filter(type__slug='district')
    entities_reported_stock = active_sps.exclude(last_reported=None)
    web_users = User.objects.filter(is_active=True)
    clinic_type = getattr(config.SupplyPointCodes,'CLINIC', 'nomatch')
    chps_type = getattr(config.SupplyPointCodes,'CHPS', 'nomatch')
    district_hospital_type = getattr(config.SupplyPointCodes,'DISTRICT_HOSPITAL', 'nomatch')
    health_center_type = getattr(config.SupplyPointCodes,'HEALTH_CENTER', 'nomatch')
    hospital_type = getattr(config.SupplyPointCodes,'HOSPITAL', 'nomatch')
    psychiatric_hospital_type = getattr(config.SupplyPointCodes,'PSYCHIATRIC_HOSPITAL', 'nomatch')
    regional_medical_store_type = getattr(config.SupplyPointCodes,'REGIONAL_MEDICAL_STORE', 'nomatch')
    regional_hospital_type = getattr(config.SupplyPointCodes,'REGIONAL_HOSPITAL', 'nomatch')
    polyclinic_type = getattr(config.SupplyPointCodes,'POLYCLINIC', 'nomatch')
    teaching_hospital_type = getattr(config.SupplyPointCodes,'TEACHING_HOSPITAL', 'nomatch')
    central_medical_store_type = getattr(config.SupplyPointCodes,'CENTRAL_MEDICAL_STORE', 'nomatch')

    context = {
        'supply_points': active_sps.count(),
        'country': country.count(),
        'region': region.count(),
        'district': district.count(),
        'entites_reported_stock': entities_reported_stock.count(),
        'clinic': active_sps.filter(type__code=clinic_type).count(),
        'chps': active_sps.filter(type__code=chps_type).count(),
        'district_hospital': active_sps.filter(type__code=district_hospital_type).count(),
        'health_center': active_sps.filter(type__code=health_center_type).count(),
        'hospital': active_sps.filter(type__code=hospital_type).count(),
        'psychiatric_hospital': active_sps.filter(type__code=psychiatric_hospital_type).count(),
        'regional_medical_store': active_sps.filter(type__code=regional_medical_store_type).count(),
        'regional_hospital': active_sps.filter(type__code=regional_hospital_type).count(),
        'polyclinic': active_sps.filter(type__code=polyclinic_type).count(),
        'teaching_hospital': active_sps.filter(type__code=teaching_hospital_type).count(),
        'central_medical_store': active_sps.filter(type__code=central_medical_store_type).count(),
        'hsas': active_sps.filter(type__code=hsa_type).count(),
        'contacts': Contact.objects.filter(is_active=True).count(),
        'product_stocks': ProductStock.objects.filter(is_active=True).count(),
        'stock_transactions': StockTransaction.objects.count(),
        'inbound_messages': Message.objects.filter(direction='I').count(),
        'outbound_messages': Message.objects.filter(direction='O').count(),
        'products': Product.objects.count(),
        'web_users': web_users.count(),
        'web_users_admin': web_users.filter(is_superuser=True).count(),
        'web_users_read_only': web_users.filter(is_superuser=False).count(),
    }

    return render_to_response('logistics/global_stats.html', context,
                              context_instance=RequestContext(request))


def redirect_view(request):
    return HttpResponseRedirect('http://commcarehq.org/a/ews-ghana/')
