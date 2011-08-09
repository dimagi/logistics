from rapidsms.tests.scripted import TestScript
import logistics.apps.ilsgateway.app as ilsgateway_app
from logistics.apps.ilsgateway.utils import *
import logistics.apps.ilsgateway.callbacks as callbacks
from logistics.apps.ilsgateway.models import Facility, District, ServiceDeliveryPoint, ServiceDeliveryPointStatusType
from datetime import datetime, date
from dateutil.relativedelta import *
from dateutil.rrule import *

from rapidsms.tests.harness import MockRouter, MockBackend
from logistics.apps.ilsgateway.tests.testcases import CreateDataTest, FlushTestScript
    
class TestCallbacks (FlushTestScript, CreateDataTest):

    def TestLastBusinessDayOfMonth(self):
        start_datetime = datetime(2010, 12, 15, 14, 0, 0)
        date_list = [datetime(2010, 11, 30, 14, 0, 0),
                     datetime(2010, 12, 31, 14, 0, 0),
                     datetime(2011, 1, 31, 14, 0, 0),
                     datetime(2011, 2, 28, 14, 0, 0),
                     datetime(2011, 3, 31, 14, 0, 0),
                     datetime(2011, 4, 29, 14, 0, 0),
                     datetime(2011, 5, 31, 14, 0, 0),
                     datetime(2011, 6, 30, 14, 0, 0),
                     datetime(2011, 7, 29, 14, 0, 0),
                     datetime(2011, 8, 31, 14, 0, 0),
                     datetime(2011, 9, 30, 14, 0, 0),
                     datetime(2011, 10, 31, 14, 0, 0),
                     datetime(2011, 11, 30, 14, 0, 0),
                     datetime(2011, 12, 30, 14, 0, 0),
                     datetime(2012, 1, 31, 14, 0, 0),
                     datetime(2012, 2, 29, 14, 0, 0),
                     datetime(2012, 3, 30, 14, 0, 0),
                     datetime(2012, 4, 30, 14, 0, 0),
                     datetime(2012, 5, 31, 14, 0, 0),
                     datetime(2012, 6, 29, 14, 0, 0),
                     datetime(2012, 7, 31, 14, 0, 0),
                     datetime(2012, 8, 31, 14, 0, 0),
                     datetime(2012, 9, 28, 14, 0, 0),
                     datetime(2012, 10, 31, 14, 0, 0),
                     datetime(2012, 11, 30, 14, 0, 0),
                     datetime(2012, 12, 31, 14, 0, 0),
                     datetime(2013, 1, 31, 14, 0, 0),
                     datetime(2013, 2, 28, 14, 0, 0),
                     datetime(2013, 3, 29, 14, 0, 0),
                     datetime(2013, 4, 30, 14, 0, 0),
                     datetime(2013, 5, 31, 14, 0, 0),
                     datetime(2013, 6, 28, 14, 0, 0),
                     datetime(2013, 7, 31, 14, 0, 0),
                     datetime(2013, 8, 30, 14, 0, 0),
                     datetime(2013, 9, 30, 14, 0, 0),
                     datetime(2013, 10, 31, 14, 0, 0),
                     datetime(2013, 11, 29, 14, 0, 0),
                     datetime(2013, 12, 31, 14, 0, 0),
                     datetime(2014, 1, 31, 14, 0, 0),
                     datetime(2014, 2, 28, 14, 0, 0),
                     datetime(2014, 3, 31, 14, 0, 0),
                     datetime(2014, 4, 30, 14, 0, 0),
                     datetime(2014, 5, 30, 14, 0, 0),
                     datetime(2014, 6, 30, 14, 0, 0),
                     datetime(2014, 7, 31, 14, 0, 0),
                     datetime(2014, 8, 29, 14, 0, 0),
                     datetime(2014, 9, 30, 14, 0, 0),
                     datetime(2014, 10, 31, 14, 0, 0),
                     datetime(2014, 11, 28, 14, 0, 0),
                     datetime(2014, 12, 31, 14, 0, 0),]
        i = 0
        while i < len(date_list) - 1:     
            start_time = start_datetime + relativedelta(months=i-1, 
                                             day=get_last_business_day_of_month((start_datetime + relativedelta(months=i-1)).year, 
                                                                                (start_datetime + relativedelta(months=i-1)).month))

            end_time = start_datetime + relativedelta(months=i,
                                                      day=get_last_business_day_of_month((start_datetime + relativedelta(months=i)).year, 
                                                                                         (start_datetime + relativedelta(months=i)).month))
                                             
            self.assertEqual(date_list[i], start_time)
            self.assertTrue(date_list[i+1], end_time)
            i = i + 1
            
    def TestLastBusinessDayOfMonthWithOffset(self):
        day = get_last_business_day_of_month(2010, 12)
        self.assertEqual(day, 31)

        day = get_last_business_day_of_month(2010, 12, -1)
        self.assertEqual(day, 30)

        day = get_last_business_day_of_month(2010, 12, -2)
        self.assertEqual(day, 29)
            
        day = get_last_business_day_of_month(2010, 12, -3)
        self.assertEqual(day, 28)
            
        day = get_last_business_day_of_month(2010, 12, -4)
        self.assertEqual(day, 27)
            
        day = get_last_business_day_of_month(2010, 12, -5)
        self.assertEqual(day, 24)
            
        day = get_last_business_day_of_month(2010, 12, -6)
        self.assertEqual(day, 23)
            
        day = get_last_business_day_of_month(2010, 12, -7)
        self.assertEqual(day, 22)
            
        day = get_last_business_day_of_month(2010, 12, -8)
        self.assertEqual(day, 21)
            
    def TestBusinessDayOnOrBeforeDate(self):
        self.assertEqual(get_last_business_day_on_or_before(datetime(2010, 12, 1, 1, 1)), datetime(2010, 12, 1, 1, 1))
        self.assertEqual(get_last_business_day_on_or_before(datetime(2010, 11, 30)), datetime(2010, 11, 30))            
        self.assertEqual(get_last_business_day_on_or_before(datetime(2010, 11, 29)), datetime(2010, 11, 29))            
        self.assertEqual(get_last_business_day_on_or_before(datetime(2010, 11, 28)), datetime(2010, 11, 26))            
        self.assertEqual(get_last_business_day_on_or_before(datetime(2010, 11, 27)), datetime(2010, 11, 26))            
        self.assertEqual(get_last_business_day_on_or_before(datetime(2010, 11, 26)), datetime(2010, 11, 26))                    
        self.assertEqual(get_last_business_day_on_or_before(datetime(2010, 11, 25)), datetime(2010, 11, 25))
        self.assertEqual(get_last_business_day_on_or_before(datetime(2010, 11, 24)), datetime(2010, 11, 24))                    
        self.assertEqual(get_last_business_day_on_or_before(datetime(2010, 11, 23)), datetime(2010, 11, 23))
        self.assertEqual(get_last_business_day_on_or_before(datetime(2010, 11, 22)), datetime(2010, 11, 22))
        self.assertEqual(get_last_business_day_on_or_before(datetime(2010, 11, 21)), datetime(2010, 11, 19))
        self.assertEqual(get_last_business_day_on_or_before(datetime(2010, 11, 20)), datetime(2010, 11, 19))
        self.assertEqual(get_last_business_day_on_or_before(datetime(2010, 11, 19)), datetime(2010, 11, 19))        
        self.assertEqual(get_last_business_day_on_or_before(datetime(2010, 11, 18)), datetime(2010, 11, 18))
        self.assertEqual(get_last_business_day_on_or_before(datetime(2011, 1, 1)), datetime(2010, 12, 31))                
        
        
    def TestOldBusinessDayOnOrBefore(self):
        now = datetime.now()
        byhour = 14
        byminute = 0
        monthday = 16
        bysetpos = -1
        rr1 = rrule(MONTHLY, 
                    interval=1, 
                    dtstart=now + relativedelta(months=-2), 
                    until=  now + relativedelta(months=+2), 
                    byweekday=(MO,TU,WE,TH,FR), 
                    byhour=byhour, 
                    bysetpos=bysetpos,
                    byminute=byminute,
                    bysecond=0,
                    bymonthday=(monthday-2, monthday-1, monthday))
        start_time = rr1.before(now)
        end_time = rr1.after(now)
        self.assertEqual(start_time, datetime(2011, 6, 16, 14))
        self.assertEqual(end_time, datetime(2011, 7, 15, 14))
        
    def TestOldLastBusinessDayOfMonthWithOffset(self):
        base_datetime = datetime(2011, 12, 15, 14, 0, 0)
        
        rr1 = rrule(MONTHLY, 
                    interval=1, 
                    dtstart=base_datetime + relativedelta(months=-2), 
                    until=  base_datetime + relativedelta(months=+2), 
                    byweekday=(MO,TU,WE,TH,FR), 
                    byhour=8, 
                    bysetpos=-7,
                    byminute=0,
                    bysecond=0)
        start_time = rr1.before(base_datetime)
        end_time = rr1.after(base_datetime)

        #The original method was off by 1 day when the last day of the month is on a weekend
        self.assertNotEqual(start_time, datetime(2011, 11, 21, 8, 0, 0))
        self.assertEqual(end_time, datetime(2011, 12, 22, 8, 0, 0))        
        
#    def TestCallBackIntegration(self):
#        self.startRouter()
#        self.router.logger.setLevel(logging.DEBUG)
#        
#        reminder_name = "soh_reminder_sent_facility"
#        
#        # 2pm
#        byhour =      14 
#        byminute =    0
#        
#        # additional reminders
#        additional_reminders_to_send = [{"additional_business_days":1, "hour": 8, "minute": 15},
#                                        {"additional_business_days":5, "hour": 8, "minute": 15}]
#        
#        #send them out
#        callbacks._send_reminders(self.router,
#                        reminder_name,
#                        None,
#                        byhour,
#                        byminute,                    
#                        additional_reminders_to_send,
#                        Facility.objects.all())
#        self.stopRouter()

    def test_district_delinquent_deliveries_summary(self):
        reminder_name = "alert_delinquent_delivery_sent_district"
    
        # 7 days prior to the last day of the month - we leave off monthday because rrule barfs on setpos/monthday conflicts
        bysetpos=     -7
        # 2pm
        byhour =      8 
        byminute =    0
    
        # additional reminders
        additional_reminders_to_send = []
        
        #send them out
        self.test_send_reminders(
                        reminder_name,
                        None, #leave out monthday
                        byhour,
                        byminute,                    
                        additional_reminders_to_send,
                        District.objects.all(),
                        bysetpos)
    
    def test_facility_soh_reminder(self):
        #Reminder window: the last weekday of the month at 2pm to the last weekday of the following month at 2pm 
        reminder_name = "soh_reminder_sent_facility"
        
        # 2pm
        byhour =      14 
        byminute =    0
        
        # additional reminders
        additional_reminders_to_send = [{"additional_business_days":1, "hour": 8, "minute": 15},
                                        {"additional_business_days":5, "hour": 8, "minute": 15}]
        
        #send them out
        self.test_send_reminders(
                        reminder_name,
                        None,
                        byhour,
                        byminute,                    
                        additional_reminders_to_send,
                        Facility.objects.all())
    
    def test_facility_adjustments_reminder(self):
        #Reminder window: the last weekday of the month at 2pm to the last weekday of the following month at 2pm
        # Same as SOH, but don't send the initial reminder since it's initiated by the SOH response
        monthday=31
        
        reminder_name = "lost_adjusted_reminder_sent_facility"
        
        # 2pm
        byhour =      14 
        byminute =    0
        
        # additional reminders
        additional_reminders_to_send = [{"additional_business_days":1, "hour": 8, "minute": 0}]
        
        #send them out
        self.test_send_reminders(
                        reminder_name,
                        monthday,
                        byhour,
                        byminute,                    
                        additional_reminders_to_send,
                        Facility.objects.all(),
                        -1,
                        False)
    
    def test_facility_supervision_reminder(self):
        #Reminder window: the last weekday of the month at 2:15pm to the last weekday of the following month at 2:15pm 
        monthday=31
        
        reminder_name = "supervision_reminder_sent_facility"
        
        # 2:15pm
        byhour =      14 
        byminute =    15
        
        # additional reminders
        additional_reminders_to_send = []
        
        #send them out
        self.test_send_reminders(
                        reminder_name,
                        monthday,
                        byhour,
                        byminute,                    
                        additional_reminders_to_send,
                        Facility.objects.all())
    
    def test_facility_randr_reminder(self):
        reminder_name = "r_and_r_reminder_sent_facility"
        
        # 5th business day of the month
        monthday =    5
        
        # 8am
        byhour =      8 
        byminute =    0
        
        # additional reminders
        additional_reminders_to_send = [{"additional_business_days":5, "hour": 8, "minute": 0},
                                        {"additional_business_days":7, "hour": 8, "minute": 0}]
        #send them out
        self.test_send_reminders(
                        reminder_name,
                        monthday,
                        byhour,
                        byminute,                    
                        additional_reminders_to_send,
                        Facility.objects.filter(delivery_group__name=current_submitting_group()))
            
    def test_district_randr_reminder(self):
        reminder_name = "r_and_r_reminder_sent_district"
    
        #The last weekday of the month prior to the 13th
        monthday =    13
        
        # 2pm
        byhour =      8 
        byminute =    0
    
        # additional reminders
        additional_reminders_to_send = [{"additional_business_days":2, "hour": 8, "minute": 0},
                                        {"additional_business_days":3, "hour": 14, "minute": 0}]
        #send them out
        self.test_send_reminders(
                        reminder_name,
                        monthday,
                        byhour,
                        byminute,                    
                        additional_reminders_to_send,
                        District.objects.all())
            
    def test_facility_delivery_reminder(self):
        reminder_name = "delivery_received_reminder_sent_facility"
    
        #The last weekday of the month prior to the 15th
        monthday =    15
        
        # 2pm
        byhour =      14 
        byminute =    0
    
        # additional reminders
        additional_reminders_to_send = [{"additional_business_days":7, "hour": 14, "minute": 0},
                                        {"additional_business_days":15, "hour": 14, "minute": 0}]
        #send them out
        self.test_send_reminders(
                        reminder_name,
                        monthday,
                        byhour,
                        byminute,
                        additional_reminders_to_send,
                        Facility.objects.filter(delivery_group__name=current_delivering_group()))
        
    def test_district_delivery_reminder(self):
        # TODO: This should skip districts that don't have any deliveries expected - for example, if there are no facilities in Group C then there won't be deliveries expected in March 
        reminder_name = "delivery_received_reminder_sent_district"
    
        #The last weekday of the month prior to the 13th at 2pm
        monthday =    13
        byhour =      14 
        byminute =    0
    
        # additional reminders
        additional_reminders_to_send = [{"additional_business_days":7, "hour": 14, "minute": 0},
                                        {"additional_business_days":15, "hour": 14, "minute": 0}]
        #send them out
        self.test_send_reminders(
                        reminder_name,
                        monthday,
                        byhour,
                        byminute,                    
                        additional_reminders_to_send,
                        District.objects.all())

    def TestRunReminders(self):    
        result = self.test_district_delinquent_deliveries_summary()
        
        self.assertEqual(result[0], result[1])
        
        test_facility_soh_reminder(router)
        
        test_facility_adjustments_reminder(router)
        
        test_facility_supervision_reminder(router)
        
        test_facility_randr_reminder(router)
        test_district_randr_reminder(router)
        
        test_facility_delivery_reminder(router)
        test_district_delivery_reminder(router)


    def test_send_reminders(self,
                        reminder_name,
                        monthday,
                        byhour,
                        byminute,                    
                        additional_reminders_to_send,
                        default_query=ServiceDeliveryPoint.objects.all(),
                        bysetpos=-1,
                        send_initial=True,
                        message_kwargs={}):
        
        now = callbacks._get_current_time()
        additional_reminders_to_send_count = len(additional_reminders_to_send)
        sdp_status_type = ServiceDeliveryPointStatusType.objects.filter(short_name=reminder_name)[0:1].get()
        
        #create a date rule (for business day logic) - last weekday prior to monthday
        if monthday:
            start_time = get_last_business_day_on_or_before(now + relativedelta(months=-1, hour = byhour, minute = byminute, microsecond=0))
            end_time = get_last_business_day_on_or_before(now + relativedelta(hour = byhour, minute = byminute, microsecond=0))
        else:
            start_time = now + relativedelta(months=-1, 
                                             day=get_last_business_day_of_month((now + relativedelta(months=-1)).year, 
                                                                                (now + relativedelta(months=-1)).month))
        
            end_time = now + relativedelta(day=get_last_business_day_of_month(now.year, 
                                                                              now.month))

        return [start_time, end_time]
