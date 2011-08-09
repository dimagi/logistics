import logging
from dateutil.rrule import *
from django.db import models
from django.db.models import Q
from rapidsms.models import ExtensibleModelBase
from rapidsms.contrib.locations.models import Location
from rapidsms.models import Contact, Connection
from django.contrib.auth.models import User
from rapidsms.contrib.messagelog.models import Message
from datetime import datetime, timedelta
from utils import *
from django.contrib.contenttypes.models import ContentType
from dateutil.relativedelta import relativedelta
from django.db.models import Max
from re import match
from django.utils.translation import ugettext as _
from djtables.cell import Cell
from djtables.column import Column, DateColumn

class ILSGatewayUser(User):
    service_delivery_point = models.ForeignKey("ServiceDeliveryPoint", null=False, default=1)    
    role = models.ForeignKey('ContactRole', null=False, default=5)

class ILSGatewayCell(Cell):
    def unicode(self):
        return unicode(self.column.render(self))

class ILSGatewayColumn(Column):
    def __init__(self, head_verbose=None, is_product=False, **kwargs):
        self.head_verbose = head_verbose
        self.is_product = is_product
        super(ILSGatewayColumn, self).__init__(**kwargs)

class ILSGatewayDateColumn(DateColumn):
    def __init__(self, head_verbose=None, **kwargs):
        self.head_verbose = head_verbose
        super(ILSGatewayDateColumn, self).__init__(**kwargs)

class DeliveryGroupManager(models.Manager):    
    def get_by_natural_key(self, name):
        return self.get(name=name)    

class DeliveryGroup(models.Model):
    objects = DeliveryGroupManager()
    name = models.CharField(max_length=100, unique=True)
    
    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ('name',)  
            
class ServiceDeliveryPointNote(models.Model):
    text = models.CharField(max_length=500)
    service_delivery_point = models.ForeignKey('ServiceDeliveryPoint')
    created_at = models.DateTimeField(auto_now_add=True)
    contact_detail = models.ForeignKey('ContactDetail')
 
class Product(models.Model):
    name = models.CharField(max_length=100)
    units = models.CharField(max_length=100)
    sms_code = models.CharField(max_length=10)
    description = models.CharField(max_length=255)
    product_code = models.CharField(max_length=100, null=True, blank=True)

    @classmethod
    def get_product(cls, product_code):
        # wrapper for handling multiple product codes w/o db changes (temnporary transition)
        if product_code.lower() == 'iucd':
            product_code = 'id' 
        elif product_code.lower() == 'depo':
            product_code = 'dp'
        elif product_code.lower() == 'impl':
            product_code = 'ip'
        elif product_code.lower() == 'coc':
            product_code = 'cc'
        elif product_code.lower() == 'pop':
            product_code = 'pp'
            
        return Product.objects.filter(sms_code__iexact=product_code)[0:1].get()
    
    def __unicode__(self):
        return self.name
    
class ServiceDeliveryPointType(models.Model):
    name = models.CharField(max_length=100)
    
    def __unicode__(self):
        return self.name


class ActiveProduct(models.Model):
    is_active = models.BooleanField(default=True)
    current_quantity = models.IntegerField(blank=True, null=True)
    service_delivery_point = models.ForeignKey('ServiceDeliveryPoint')
    product = models.ForeignKey('Product')

class ServiceDeliveryPointManager(models.Manager):    
    def get_by_natural_key(self, name):
        return self.get(name=name)    
    
class ServiceDeliveryPoint(Location):
    """
    ServiceDeliveryPoint - the main concept of a location.  Currently covers MOHSW, Regions, Districts and Facilities.  This could/should be broken out into subclasses.
    """
    @property
    def label(self):
        """
        Return an HTML fragment, for embedding in a Google map. This
        method should be overridden by subclasses wishing to provide
        better contextual information.
        """
        return unicode(self)
    
    objects = ServiceDeliveryPointManager()
    sdp_name = models.CharField(max_length=100, blank=True)
    active = models.BooleanField(default=True)
    delivery_group = models.ForeignKey(DeliveryGroup, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    products = models.ManyToManyField(Product, through='ServiceDeliveryPointProductReport')
    msd_code = models.CharField(max_length=100, blank=True, null=True)
    service_delivery_point_type = models.ForeignKey(ServiceDeliveryPointType)    
    
    @property
    def name(self):
        return self.sdp_name

    def stock_levels_array(self):
        soh_array = []
        for product in Product.objects.all():
            soh_value = self.stock_on_hand(product.sms_code)
            if soh_value == None:
                soh_value = "No data"
            mos_value = self.months_of_stock(product.sms_code)
            if mos_value == None:
                mos_value = "Insufficient data"
            soh_array.append([product.sms_code, soh_value, mos_value])
        return soh_array
            
    def contacts(self, contact_type='all'):
        if contact_type == 'all':
            return ContactDetail.objects.filter(service_delivery_point=self)
        elif contact_type == 'primary':
            return ContactDetail.objects.filter(service_delivery_point=self, primary=True)
        elif contact_type == 'secondary':
            return ContactDetail.objects.filter(service_delivery_point=self, primary=False)
        else:
            return []

    def child_sdps_contacts(self):
        return ContactDetail.objects.filter(service_delivery_point__parent_id=self.id)        

    def primary_contacts(self):
        return self.contacts('primary')

    def secondary_contacts(self):
        return self.contacts('secondary')

    def received_reminder_after(self, short_name, date):
        result_set = self.servicedeliverypointstatus_set.filter(status_type__short_name=short_name, 
                                                      status_date__gt=date)
        if result_set:
            return True
        else:
            return False
    
    def report_product_status(self, **kwargs):
        npr = ServiceDeliveryPointProductReport(service_delivery_point = self,  **kwargs)
        npr.save()
        
    def report_delivery_group_status(self, **kwargs):
        sdp_dgr = ServiceDeliveryPointDGReport(service_delivery_point = self,  **kwargs)
        sdp_dgr.save()        
        
    def randr_status(self, report_date=datetime.now() ):
        try:
            status = self.servicedeliverypointstatus_set.filter(status_type__short_name__startswith='r_and_r',
                                                                status_date__range=(report_date + relativedelta(day=31, minute=59, second=59, hour=23, microsecond=999999, months=-1),
                                                                                    report_date + relativedelta(day=31, minute=59, second=59, hour=23, microsecond=999999) )).latest()
            return status
        except:
            return None

    def randr_status_by_quarter(self, 
                                report_date=datetime.now() ):
        print report_date
        try:
            if report_date.month <= 3:
                report_date_start = datetime(report_date.year, 1, 1)
                report_date_end = datetime(report_date.year, 4, 1)
            elif report_date.month <= 6:
                report_date_start = datetime(report_date.year, 4, 1)
                report_date_end = datetime(report_date.year, 7, 1)
            elif report_date.month <= 9:
                report_date_start = datetime(report_date.year, 7, 1)
                report_date_end = datetime(report_date.year, 10, 1)
            else:
                report_date_start = datetime(report_date.year, 10, 1)
                report_date_end = datetime(report_date.year+1, 1, 1)

            status = self.servicedeliverypointstatus_set.filter(status_type__short_name__startswith='r_and_r',
                                                                status_date__range=(report_date_start,
                                                                                    report_date_end)).latest()
            return status
        except:
            return None
    
    def delivery_status(self, report_date=datetime.now() ):
        try:
            status = self.servicedeliverypointstatus_set.filter(status_type__short_name__startswith='delivery',
                                                                status_date__range=(report_date + relativedelta(day=31, minute=59, second=59, hour=23, microsecond=999999, months=-1),
                                                                                    report_date + relativedelta(day=31, minute=59, second=59, hour=23, microsecond=999999) )).latest()
            return status
        except:
            return None
        
    def supervision_status(self, report_date=datetime.now() ):
        try:
            status = self.servicedeliverypointstatus_set.filter(status_type__short_name__startswith='supervision',
                                                                status_date__range=(report_date + relativedelta(day=31, minute=59, second=59, hour=23, microsecond=999999, months=-1),
                                                                                    report_date + relativedelta(day=31, minute=59, second=59, hour=23, microsecond=999999) )).latest()
            return status
        except:
            return None
    
    def get_products(self):
        return Product.objects.filter(servicedeliverypoint=self.id).distinct()
    
    def last_message_received(self):
        reports = ServiceDeliveryPointProductReport.objects.filter(service_delivery_point__id=self.id, report_type__id=1).order_by('-report_date')
        if reports:
            return reports[0].message
        
    def child_sdps(self):
        return ServiceDeliveryPoint.objects.filter(parent_id=self.id)
    
    #Delivery
    def child_sdps_receiving(self, report_date=datetime.now() ):
        return self.child_sdps().filter(delivery_group__name=current_delivering_group(report_date.month))

    def child_sdps_received_delivery_this_month(self,
                                                report_date=datetime.now() ):
        return self._sdps_with_latest_status("delivery_received_facility", report_date).count() + \
               self._sdps_with_latest_status("delivery_quantities_reported", report_date).count()

    def child_sdps_not_received_delivery_this_month(self,
                                                    report_date=datetime.now() ):
        return self._sdps_with_latest_status("delivery_not_received_facility", report_date).count()

    def child_sdps_not_responded_delivery_this_month(self,
                                                     report_date=datetime.now() ):
        return self._sdps_with_latest_status("delivery_received_reminder_sent_facility", report_date).count()

    #R&R
    def child_sdps_submitting(self, report_date=datetime.now() ):
        return self.child_sdps().filter(delivery_group__name=current_submitting_group(report_date.month))

    def count_child_sdps_no_randr_reminder_sent(self,                                               
                                          start_time=datetime.now() + relativedelta(day=31, minute=59, second=59, hour=23, microsecond=999999, months=-1),
                                          end_time= datetime.now()):
        return self.child_sdps_submitting().exclude(servicedeliverypointstatus__status_type__short_name__startswith="r_and_r",
                                                    servicedeliverypointstatus__status_date__range=(start_time, end_time)).count()

    def child_sdps_submitted_randr_this_month(self,
                                              report_date=datetime.now() ):
        return self._sdps_with_latest_status("r_and_r_submitted_facility_to_district",
                                             report_date).count()

    def child_sdps_not_submitted_randr_this_month(self,
                                                  report_date=datetime.now() ):
        return self._sdps_with_latest_status("r_and_r_not_submitted_facility_to_district",
                                             report_date).count()

    def child_sdps_not_responded_randr_this_month(self,
                                                  report_date=datetime.now() ):
        return self._sdps_with_latest_status("r_and_r_reminder_sent_facility",
                                             report_date).count()

    def _sdps_with_latest_status(self, 
                                 status_short_name, 
                                 report_date=datetime.now()): 
        start_time=report_date + relativedelta(day=31, minute=59, second=59, hour=23, microsecond=999999, months=-1)
        end_time= report_date + relativedelta(day=31, minute=59, second=59, hour=23, microsecond=999999)
        if match('r_and_r', status_short_name):
            sdps = self.child_sdps_submitting(report_date)
            startswith = 'r_and_r'
        elif match('delivery', status_short_name):
            sdps = self.child_sdps_receiving()
            startswith = 'delivery'
        elif match('soh', status_short_name):
            sdps = self.child_sdps()
            startswith = 'soh'
        status_type_id = ServiceDeliveryPointStatusType.objects.get(short_name=status_short_name).id
        inner_qs = sdps.filter(servicedeliverypointstatus__status_date__range=(start_time, end_time),
                    servicedeliverypointstatus__status_type__short_name__startswith=startswith) \
                    .annotate(pk=Max('servicedeliverypointstatus__id'))
        sdp_status = ServiceDeliveryPointStatus.objects.filter(id__in=inner_qs.values('pk').query,
                                                               status_type__id=status_type_id).distinct()
        return sdp_status

    def child_sdps_processing_sent_to_msd(self, report_date=datetime.now()):
        start_time=report_date + relativedelta(day=31, minute=59, second=59, hour=23, microsecond=999999, months=-1)
        end_time= report_date + relativedelta(day=31, minute=59, second=59, hour=23, microsecond=999999)
        
        sdp_dgr_list = ServiceDeliveryPointDGReport.objects.filter(delivery_group__name=current_processing_group(), 
                                                                   report_date__range=( start_time, end_time ),
                                                                   service_delivery_point__id=self.id )
        if not sdp_dgr_list:
            return 0
        else:
            return sdp_dgr_list[0].quantity
    
    def count_child_sdps_submitting_no_primary_contact(self):
        return self.child_sdps_submitting().count() - self.child_sdps_submitting().filter(contactdetail__primary=True).count()
    
    def child_sdps_processing(self, report_date=datetime.now() ):
        return self.child_sdps().filter(delivery_group__name=current_processing_group(report_date.month))

    #SOH
    def child_sdps_not_responded_soh_this_month(self,
                                                report_date=datetime.now() ):
        return self._sdps_with_latest_status("soh_reminder_sent_facility",
                                             report_date).count()
    
    def child_sdps_responded_soh(self, report_date=datetime.now() ):
        start_time=report_date + relativedelta(day=31, minute=59, second=59, hour=23, microsecond=999999, months=-1)
        end_time= report_date + relativedelta(day=31, minute=59, second=59, hour=23, microsecond=999999)        
        
        return self.child_sdps().filter(servicedeliverypointproductreport__report_date__range=( start_time, end_time )).distinct().count()   
    
    def child_sdps_stocked_out(self, 
                               sms_code,
                               end_date=datetime.now()):
        inner_qs = self.child_sdps().filter(servicedeliverypointproductreport__product__sms_code=sms_code,
                                            servicedeliverypointproductreport__report_date__lt=end_date) \
                    .annotate(pk=Max('servicedeliverypointproductreport__id'))
        sdps = ServiceDeliveryPoint.objects.filter(servicedeliverypointproductreport__id__in=inner_qs.values('pk').query,
                                                   servicedeliverypointproductreport__quantity=0).distinct()
        return sdps
    
    def child_sdps_not_stocked_out(self, sms_code, report_date=datetime.now() ):
        start_time=report_date + relativedelta(day=31, minute=59, second=59, hour=23, microsecond=999999, months=-1)
        end_time= report_date + relativedelta(day=31, minute=59, second=59, hour=23, microsecond=999999)
        
        return self.child_sdps().filter(servicedeliverypointproductreport__product__sms_code=sms_code,
                                        servicedeliverypointproductreport__quantity__gt=0,
                                        servicedeliverypointproductreport__report_date__range=( start_time, 
                                                                                                end_time )).distinct().count()
    
    def child_sdps_no_stock_out_data(self, sms_code, report_date):
        return self.child_sdps().count() - self.child_sdps_not_stocked_out(sms_code, report_date) - self.child_sdps_stocked_out(sms_code, report_date).count()

    def child_sdps_percentage_reporting_stock_this_month(self):
        if self.child_sdps().count() > 0:
            percentage = ( (self.child_sdps_responded_soh() * 100 ) / self.child_sdps().count() )
        else:
            percentage = 0  
        return "%d " % percentage

    def child_sdps_percentage_reporting_stock_last_month(self):
        now = datetime.now()
        report_date =  now + relativedelta(months=-1)

        if self.child_sdps().count() > 0:
            percentage = ( (self.child_sdps_responded_soh(report_date) * 100 ) / self.child_sdps().count() ) 
        else:
            percentage = 0
        return "%d " % percentage
    
    def lost_adjusted(self, sms_code):
        reports = ServiceDeliveryPointProductReport.objects.filter(service_delivery_point__id=self.id,
                                                product__sms_code=sms_code,
                                                report_type__sms_code="la") 
        if reports:
            return reports[0].quantity                                 
        else:
            return 0        

    def months_of_stock(self, sms_code, report_date=datetime.now() ):
        monthly_consumption = self.calculate_monthly_consumption(sms_code)
        stock_on_hand = self.stock_on_hand(sms_code, report_date)
        if stock_on_hand:
            if monthly_consumption > 0:
                return round(stock_on_hand / monthly_consumption, 1)
            else:
                return 0
        else:
            return None
        
    def calculate_monthly_consumption(self, sms_code):
        # This maybe become be a performance hog, could a) cache or b) refactor
        
        #TODO This needs to be a setting or a db value
        months_to_calculate = 3
        # Calculate consumption for the X months prior, then calculate latest stock levels divided by avg monthly consumption
        now = datetime.now()
        rr1 = rrule(MONTHLY, 
                    interval=1, 
                    dtstart=now + relativedelta(months=-(months_to_calculate+1)), 
                    count=months_to_calculate+2,
                    byweekday=(MO,TU,WE,TH,FR), 
                    byhour=14, 
                    bysecond=0,
                    bysetpos=-1,
                    byminute=0)
            
        reports = ServiceDeliveryPointProductReport.objects.filter(Q(service_delivery_point__id=self.id,
                                                                  report_type__sms_code__in=['soh', 'la', 'dlvd'],
                                                                  product__sms_code=sms_code,
                                                                  report_date__range=(rr1[0], now))).order_by('report_date')
        if reports:
            logging.debug(list(rr1))
            consumption_list = []
            for i in range(months_to_calculate):
                current_month_vals = {}
                logging.debug("Calcing consumption for period %s to %s" % (rr1[i+1], rr1[i+2]))
                # calc closing balance from last month (current cycles' opening balance)
                report_type = 'soh'
                current_month_reports = reports.filter(report_date__range=(rr1[i], rr1[i+1]),
                                                       report_type__sms_code=report_type)
                if current_month_reports:
                    latest_report = current_month_reports.latest('report_date')
                    logging.debug("  Closing balance for period ending %s reported on %s: %s" % (rr1[i], latest_report.report_date, latest_report.quantity))
                    if report_type == 'soh':
                        current_month_vals['opening_balance'] = latest_report.quantity
                    elif report_type == 'la':
                        current_month_vals['adjustments'] = latest_report.quantity
                else:                        
                    if report_type == 'soh':
                        current_month_vals['opening_balance'] = 0
                    elif report_type == 'la':
                        current_month_vals['adjustments'] = 0
                
                # calculate received, adjustments and opening balance for the next month        
                for report_type in ['soh', 'dlvd', 'la']:                        
                    current_month_reports = reports.filter(report_date__range=(rr1[i+1], rr1[i+2]),
                                                           report_type__sms_code=report_type)
                    if current_month_reports:
                        latest_report = current_month_reports.latest('report_date')
                        logging.debug("  %s for period ending %s reported on %s: %s" % (report_type, rr1[i+1], latest_report.report_date, latest_report.quantity))
                        current_month_vals[report_type] = latest_report.quantity
                    else:                        
                        current_month_vals[report_type] = 0

                if current_month_vals['opening_balance'] == 0 or current_month_vals['soh'] == 0:
                    consumption = None
                else:
                    consumption = current_month_vals['opening_balance'] + current_month_vals['dlvd'] + current_month_vals['la'] - current_month_vals['soh'] 
                if consumption is not None:
                    consumption_list.append(consumption)
            if len(consumption_list) > 0:
                avg_consumption =  sum([i for i in consumption_list]) / float(len(consumption_list))
                return avg_consumption
            else:
                return None

    def stock_on_hand(self, sms_code, end_date=datetime.now() + relativedelta(months=-1) ):
        start_time = end_date + relativedelta(months=-1, 
                                         day=get_last_business_day_of_month((end_date + relativedelta(months=-1)).year, 
                                                                            (end_date + relativedelta(months=-1)).month))
    
        end_time = end_date + relativedelta(day=get_last_business_day_of_month(end_date.year, 
                                                                          end_date.month))
        
        reports = ServiceDeliveryPointProductReport.objects.filter(report_date__range=(start_time, end_time ),
                                                                   service_delivery_point__id=self.id,
                                                                   product__sms_code=sms_code,
                                                                   report_type__sms_code="soh") 
        if reports:
            return reports[0].quantity                                 
        else:
            return None        
    
    def stock_on_hand_last_reported(self, date_before=datetime.now() ):
        reports = ServiceDeliveryPointProductReport.objects.filter(service_delivery_point__id=self.id,
                                                                   report_type__id=1,
                                                                   report_date__lt=date_before) 
        if reports:
            return reports[0].report_date                                 
        elif self.received_reminder_after("soh_reminder_sent_facility", 
                                          datetime.now() + relativedelta(day=31, minute=59, second=59, hour=23, microsecond=999999, months=-1)):
            return "Waiting for reply"           
        else:
            return "No reminder sent"       

    def child_sdps_without_contacts(self):
        return self.child_sdps().filter(contactdetail__primary__isnull=True).order_by('name')[:3]

    def __unicode__(self):
        return self.name

class MinistryOfHealth(ServiceDeliveryPoint):
    class Meta:
        verbose_name_plural = "Ministry of Health"  

    pass
    
class Region(ServiceDeliveryPoint):
    pass

class District(ServiceDeliveryPoint):
    pass

class Facility(ServiceDeliveryPoint):
    class Meta:
        verbose_name_plural = "Facilities"  
    
    pass
    
class ContactRole(models.Model):
    name = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = "Role"

    def __unicode__(self):
        return _(self.name)

class ContactDetail(Contact):
    user = models.OneToOneField(ILSGatewayUser, null=True, blank=True, help_text="The user associated with this Contact Detail.  Not every Contact Detail has the ability to login, so assigning or creating a username for a Contact Detail gives the user the ability to login to the sytem.")
    cd_role = models.ForeignKey(ContactRole, null=True, blank=True)
    email = models.EmailField(blank=True)
    #TODO validate only one primary can exist (or auto change all others to non-primary when new primary selected)
    service_delivery_point = models.ForeignKey(ServiceDeliveryPoint,null=True,blank=True)
    primary = models.BooleanField(default=False)
    
    @property
    def role(self):
        return self.cd_role

    def allowed_to_edit(self, current_sdp):
        parent_service_delivery_points_ids = []
        while current_sdp is not None:
            parent_service_delivery_points_ids.append(current_sdp.id)
            current_sdp = current_sdp.parent 
        return self.service_delivery_point.id in parent_service_delivery_points_ids
    
    def is_mohsw_level(self):
        return self.role.name in ["MOHSW", "MSD"]
    
    def phone(self):
        if self.default_connection:
            return self.default_connection.identity
        else:
            return " "
    
    def role_name(self):
        return self.role.name

    def service_delivery_point_name(self):
        return self.service_delivery_point.name
    
    class Meta:
        verbose_name = "Contact Detail"
    
    def __unicode__(self):
        return self.name
        
class ProductReportType(models.Model):
    name = models.CharField(max_length=100)
    sms_code = models.CharField(max_length=10)

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = "Inventory Status Type" 
    
class ServiceDeliveryPointProductReport(models.Model):
    product = models.ForeignKey(Product)
    service_delivery_point = models.ForeignKey(ServiceDeliveryPoint)
    report_type = models.ForeignKey(ProductReportType)
    quantity = models.IntegerField()  
    report_date = models.DateTimeField(auto_now_add=True, default=datetime.now())
    message = models.ForeignKey(Message)  
    
    def product_name(self):
        return self.product.name
    
    def service_delivery_point_name(self):
        return self.service_delivery_point.name

    def report_type_name(self):
        return self.report_type.name

    def __unicode__(self):
        return self.service_delivery_point.name + '-' + self.product.name + '-' + self.report_type.name

    class Meta:
        verbose_name = "Inventory Status Report" 
        ordering = ('-report_date',)

class ServiceDeliveryPointDGReport(models.Model):
    service_delivery_point = models.ForeignKey(ServiceDeliveryPoint)
    quantity = models.IntegerField()  
    report_date = models.DateTimeField(auto_now_add=True, default=datetime.now())
    message = models.ForeignKey(Message)  
    delivery_group = models.ForeignKey(DeliveryGroup)
    
    class Meta:
        ordering = ('-report_date',)
        
class ServiceDeliveryPointStatusType(models.Model):
    """
    This is the status for both R&R process and delivery - could be given a process name field to clarify between the two.
    """
    
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=100)

    class Meta:
        verbose_name = "Facility Status Type"

    def __unicode__(self):
        return self.name    

class ServiceDeliveryPointStatus(models.Model):
    status_type = models.ForeignKey(ServiceDeliveryPointStatusType)
    #message = models.ForeignKey(Message)
    status_date = models.DateTimeField()
    service_delivery_point = models.ForeignKey(ServiceDeliveryPoint) 
        
    def status_type_name(self):
        return self.status_type.name
    
    def service_delivery_point_name(self):
        return self.service_delivery_point.name
    
    def __unicode__(self):
        return self.status_type.name
    
    class Meta:
        verbose_name = "Facility Status"
        verbose_name_plural = "Facility Statuses"  
        get_latest_by = "status_date"  
        ordering = ('-status_date',) 
