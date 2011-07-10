from datetime import datetime, timedelta
import logging
import os
from rapidsms.contrib.locations.models import Location
from rapidsms.models import Contact
from logistics.models import ProductReport, ProductReportType, SupplyPoint,\
    SupplyPointType, NagRecord, ContactRole, StockRequest, StockRequestStatus
from celery.schedules import crontab
from celery.decorators import periodic_task
from rapidsms.contrib.messaging.utils import send_message
from logistics.const import Reports
from logistics import config
from static.malawi.config import Messages
from logistics_project.apps.malawi.util import hsa_supply_points_below

DAYS_BETWEEN_FIRST_AND_SECOND_WARNING = 3
DAYS_BETWEEN_SECOND_AND_THIRD_WARNING = 2
DAYS_BETWEEN_THIRD_AND_FOURTH_WARNING = 2
REC_DAYS_BETWEEN_FIRST_AND_SECOND_WARNING = 3
REC_DAYS_BETWEEN_SECOND_AND_THIRD_WARNING = 4

EM_REPORTING_DAY = 1 # First of the month
WARNING_DAYS = 2 # Advance warning days before report is officially late

def get_non_reporting_hsas(since, report_code=Reports.SOH, location=None):
    """
    Get all HSAs who haven't reported since a passed in date
    """
    hsas = set(hsa_supply_points_below(location))
    reporters = set(x.supply_point for x in \
                    ProductReport.objects.filter(report_type=ProductReportType.objects.get(code=report_code),
                                                 report_date__range = [since,
                                                                       datetime.utcnow()]))
    return hsas - reporters

def nag_hsas_soh(since, location=None):
    """
    Send non-reporting HSAs a predefined nag message.  Notify their supervisor if they've been
    sufficiently delinquent.
    """
    hsas = get_non_reporting_hsas(since, Reports.SOH, location)
    hsa_first_warnings = hsas - set(x.supply_point for x in NagRecord.objects.filter(report_date__range = [since,
                                                                               datetime.utcnow()],
                                                                                nag_type=Reports.SOH))
    hsa_second_warnings = hsas.intersection(x.supply_point for x in \
                NagRecord.objects.filter(report_date__range = [since,
                                                               datetime.utcnow()-timedelta(days=DAYS_BETWEEN_FIRST_AND_SECOND_WARNING)],
                                         warning = 1,
                                         nag_type=Reports.SOH))
    hsa_third_warnings = hsas.intersection(x.supply_point for x in \
                NagRecord.objects.filter(report_date__range = [since,
                                                               datetime.utcnow()-timedelta(days=DAYS_BETWEEN_SECOND_AND_THIRD_WARNING)],
                                         warning = 2,
                                         nag_type=Reports.SOH))
    hsa_fourth_warnings = hsas.intersection(x.supply_point for x in \
                NagRecord.objects.filter(report_date__range = [since,
                                                               datetime.utcnow()-timedelta(days=DAYS_BETWEEN_THIRD_AND_FOURTH_WARNING)],
                                         warning = 3,
                                         nag_type=Reports.SOH))
    warnings = [
            {'hsas': hsa_first_warnings,
             'number': 1,
             'days': WARNING_DAYS,
             'code': Reports.SOH,
             'message': Messages.HSA_NAG_FIRST,
             'flag_supervisor' : False},
            {'hsas': hsa_second_warnings,
             'number': 2,
             'days': DAYS_BETWEEN_FIRST_AND_SECOND_WARNING,
             'code': Reports.SOH,
             'message': Messages.HSA_NAG_SECOND,
             'flag_supervisor': False},
            {'hsas': hsa_third_warnings,
             'number': 3,
             'days': DAYS_BETWEEN_SECOND_AND_THIRD_WARNING,
             'code': Reports.SOH,
             'message': Messages.HSA_NAG_THIRD,
             'flag_supervisor': True,
             'supervisor_message': Messages.HSA_SUPERVISOR_NAG},
            {'hsas': hsa_fourth_warnings,
             'number': 4,
             'days': DAYS_BETWEEN_THIRD_AND_FOURTH_WARNING,
             'code': Reports.SOH,
             'message': Messages.HSA_NAG_THIRD, # Same messages
             'flag_supervisor': True,
             'supervisor_message': Messages.HSA_SUPERVISOR_NAG}
            ]

    send_nag_messages(warnings)

def nag_hsas_rec(since):
    """
    Send non-reporting HSAs a predefined nag message.  Notify their supervisor if they've been
    sufficiently delinquent.
    """
    hsas = set([x.supply_point for x in StockRequest.objects.filter(status=StockRequestStatus.APPROVED,
                                                                    responded_on__range = [since, datetime.utcnow()])])
    hsa_first_warnings = hsas - set(x.supply_point for x in NagRecord.objects.filter(report_date__range = [since,
                                                                               datetime.utcnow()], nag_type=Reports.REC))
    hsa_second_warnings = hsas.intersection(x.supply_point for x in \
                NagRecord.objects.filter(report_date__range = [since,
                                                               datetime.utcnow()-timedelta(days=DAYS_BETWEEN_FIRST_AND_SECOND_WARNING)],
                                         warning = 1,
                                         nag_type=Reports.REC))
    hsa_third_warnings = hsas.intersection(x.supply_point for x in \
                NagRecord.objects.filter(report_date__range = [since,
                                                               datetime.utcnow()-timedelta(days=DAYS_BETWEEN_SECOND_AND_THIRD_WARNING)],
                                         warning = 2,
                                         nag_type=Reports.REC))
    warnings = [
            {'hsas': hsa_first_warnings,
             'number': 1,
             'days': 0,
             'code': Reports.REC,
             'message': Messages.HSA_RECEIPT_NAG_FIRST,
             'flag_supervisor': False},
            {'hsas': hsa_second_warnings,
             'number': 2,
             'days': REC_DAYS_BETWEEN_FIRST_AND_SECOND_WARNING,
             'code': Reports.REC,
             'message': Messages.HSA_RECEIPT_NAG_SECOND,
             'flag_supervisor': True,
             'supervisor_message': Messages.HSA_RECEIPT_SUPERVISOR_NAG},
             {'hsas': hsa_third_warnings,
             'number': 3,
             'days': REC_DAYS_BETWEEN_SECOND_AND_THIRD_WARNING,
             'code': Reports.REC,
             'message': Messages.HSA_RECEIPT_NAG_THIRD,
             'flag_supervisor': True,
             'supervisor_message': Messages.HSA_RECEIPT_SUPERVISOR_NAG}
            ]
    send_nag_messages(warnings)


def send_nag_messages(warnings):
    for w in warnings:
        for hsa in w["hsas"]:
            try:
                contact = Contact.objects.get(supply_point=hsa)
                send_message(contact.default_connection, w["message"] % {'hsa': contact.name, 'days': w['days']})
                NagRecord(supply_point=hsa, warning=w["number"],nag_type=w['code']).save()
            except Contact.DoesNotExist:
                logging.error("Contact does not exist for HSA: %s" % hsa.name)
            if w["flag_supervisor"]:
                try:
                    supervisor = Contact.objects.get(is_active=True,
                                                     role=ContactRole.objects.get(code=config.Roles.HSA_SUPERVISOR),
                                                     supply_point=hsa.supplied_by)
                    send_message(supervisor.default_connection, w["supervisor_message"] % { 'hsa': contact.name})
                except Contact.DoesNotExist:
                    logging.error("Supervisor does not exist for HSA: %s" % hsa.name)


def nag_hsas_ept():
    since = datetime.utcnow() - timedelta(days=30-WARNING_DAYS)
    locs = [Location.objects.get(name=loc) for loc in config.Groups.GROUPS[config.Groups.EPT]]
    for l in locs:
        nag_hsas_soh(since, l)
    nag_hsas_rec(since)

def nag_hsas_em():
    since = datetime.utcnow().replace(day=EM_REPORTING_DAY) - timedelta(days=WARNING_DAYS)
    if since > datetime.utcnow():
        try:
            since.replace(month=datetime.utcnow().month - 1) # wraparound?
        except ValueError:
            since.replace(year=datetime.utcnow().year - 1, month=12)
    locs = [Location.objects.get(name=loc) for loc in config.Groups.GROUPS[config.Groups.EM]]
    for l in locs:
        nag_hsas_soh(since, l)
    nag_hsas_rec(since)

