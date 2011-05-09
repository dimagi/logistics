from datetime import datetime, timedelta
import logging
import os
from rapidsms.models import Contact
from logistics.apps.logistics.models import ProductReport, ProductReportType, SupplyPoint,\
    SupplyPointType, NagRecord, ContactRole
from celery.schedules import crontab
from celery.decorators import periodic_task
from rapidsms.contrib.messaging.utils import send_message
from logistics.apps.logistics.const import Reports
from logistics.apps.logistics.util import config
from config import Messages

DAYS_BETWEEN_FIRST_AND_SECOND_WARNING = 2
DAYS_BETWEEN_SECOND_AND_THIRD_WARNING = 2


def get_non_reporting_hsas(since):
    """
    Get all HSAs who haven't reported since a passed in date
    """
    hsas = set(SupplyPoint.objects.filter(type=SupplyPointType.objects.get(code='hsa')))
    reporters = set(x.supply_point for x in \
                    ProductReport.objects.filter(report_type=ProductReportType.objects.get(code=Reports.SOH),
                                                 report_date__range = [since,
                                                                       datetime.utcnow()]))
    return hsas - reporters

def nag_hsas(since):
    """
    Send non-reporting HSAs a predefined nag message.  Notify their supervisor if they've been
    sufficiently delinquent.
    """
    hsas = get_non_reporting_hsas(since)
    hsa_first_warnings = hsas - set(x.supply_point for x in NagRecord.objects.filter(report_date__range = [since,
                                                                               datetime.utcnow()]))
    hsa_second_warnings = hsas.intersection(x.supply_point for x in \
                NagRecord.objects.filter(report_date__range = [since,
                                                               datetime.utcnow()-timedelta(days=DAYS_BETWEEN_FIRST_AND_SECOND_WARNING)],
                                         warning = 1))
    hsa_third_warnings = hsas.intersection(x.supply_point for x in \
                NagRecord.objects.filter(report_date__range = [since,
                                                               datetime.utcnow()-timedelta(days=DAYS_BETWEEN_SECOND_AND_THIRD_WARNING)],
                                         warning = 2))


    for hsa in hsa_first_warnings:
        try:
            contact = Contact.objects.get(supply_point=hsa)
            send_message(contact.default_connection, Messages.HSA_NAG_FIRST % {'hsa': contact.name, 'days': DAYS_BETWEEN_FIRST_AND_SECOND_WARNING})
            NagRecord(supply_point=hsa, warning=1).save()
        except Contact.DoesNotExist:
            logging.error("Contact does not exist for HSA: %s" % hsa.name)

    for hsa in hsa_second_warnings:
        try:
            contact = Contact.objects.get(supply_point=hsa)
            send_message(contact.default_connection, Messages.HSA_NAG_SECOND % {'hsa': contact.name})
            NagRecord(supply_point=hsa, warning=2).save()
        except Contact.DoesNotExist:
            logging.error("Contact does not exist for HSA: %s" % hsa.name)

    for hsa in hsa_third_warnings:
            try:
                contact = Contact.objects.get(supply_point=hsa)
                send_message(contact.default_connection, Messages.HSA_NAG_THIRD % {
                            'hsa': contact.name})
                NagRecord(supply_point=hsa, warning=3).save()
            except Contact.DoesNotExist:
                logging.error("Contact does not exist for HSA: %s" % hsa.name)
            try:
                supervisor = Contact.objects.get(role=ContactRole.objects.get(code=config.Roles.IN_CHARGE),
                                                 supply_point=hsa.supplied_by)
                send_message(supervisor.default_connection, Messages.HSA_SUPERVISOR_NAG % {
                            'hsa': contact.name})
            except Contact.DoesNotExist:
                logging.error("Supervisor does not exist for HSA: %s" % hsa.name)


@periodic_task(run_every=crontab(hour="*", minute="1", day_of_week="*"))
def nag_hsas_last_month():
    return nag_hsas(datetime.utcnow() - timedelta(days=32))


@periodic_task(run_every=crontab(hour="*", minute="*", day_of_week="*"))
def heartbeat():
    if os.name == 'posix':
        f = open('/tmp/sc4ccm-heartbeat', 'w')
        f.write(str(datetime.now()))
        f.close()