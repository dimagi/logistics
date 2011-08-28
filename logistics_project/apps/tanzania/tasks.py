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
    
                         
