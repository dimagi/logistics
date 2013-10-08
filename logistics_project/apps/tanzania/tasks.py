""" This is where we actually schedule when and how often reports get run """

from celery.decorators import task
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.conf import settings
import subprocess
import tempfile
import os
from subprocess import PIPE
from django.core.mail.message import EmailMessage
from rapidsms.models import Contact
from logistics_project.apps.tanzania.config import SupplyPointCodes
from logistics.models import SupplyPoint
from logistics_project.apps.tanzania.reminders import send_message

@task
def email_report(location_code, to):
    urlbase = Site.objects.get_current().domain
    full_url='%(base)s%(path)s?place=%(loc)s&magic_token=%(token)s' % \
         {"base": urlbase, "path": reverse("tz_pdf_reports"), 
          "loc": location_code, "token": settings.MAGIC_TOKEN}
    fd, tmpfilepath = tempfile.mkstemp(suffix=".pdf", prefix="report-%s" % location_code)
    os.close(fd)
    command = 'wkhtmltopdf "%(url)s" %(file)s' % {"url": full_url, "file": tmpfilepath}
    p = subprocess.Popen(command, stdout=PIPE, stderr=PIPE, shell=True)
    p.communicate()
    email = EmailMessage('%s Report' % location_code, 'See attachment', 
                         settings.EMAIL_LOGIN, to)
    email.attach_file(tmpfilepath)
    email.send(fail_silently=False)


@task
def send_facility_list_sms(facilities, message):
    contact_list = Contact.objects.filter(
        supply_point__type__code=SupplyPointCodes.FACILITY,
        is_active=True,
        supply_point__in=facilities,
    )

    for contact in contact_list:
        send_message(
            contact,
            message
        )


@task
def send_reporting_group_list_sms(reporting_groups, message):
    for group in reporting_groups:
        facilities = SupplyPoint.objects.filter(groups__code=group)
        send_facility_list_sms(facilities, message)


@task
def send_district_list_sms(district_list, message):
    for district in district_list:
        send_facility_list_sms(district.get_children(), message)


@task
def send_region_list_sms(region_list, message):
    for region in region_list:
        send_district_list_sms(region.get_children(), message)
