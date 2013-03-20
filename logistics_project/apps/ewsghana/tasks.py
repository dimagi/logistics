import os
import tempfile
from celery.task import task
from django.core.servers.basehttp import FileWrapper
from dimagi.utils import csv 
from soil.util import expose_download
from auditcare.models import AccessAudit
from logistics_project.apps.ewsghana.views import _prep_audit_for_display

@task
def export_auditor(download_id, expiry=10*60*60):
    auditEvents = AccessAudit.view("auditcare/by_date_access_events", 
                                   descending=True, include_docs=True).all()
    detailedEvents = _prep_audit_for_display(auditEvents)
    fd, path = tempfile.mkstemp()
    with os.fdopen(fd, "w") as f:
        writer = csv.UnicodeWriter(f)
        writer.writerow(["Date ", "User", "Access_Type", "Designation", 
                         "Organization", "Facility", "Location", 
                         "First_Name", "Last_Name"])
        for e in detailedEvents:
            writer.writerow([e['date'], e['user'], e['class'], e['designation'], 
                            e['organization'], e['facility'], e['location'], 
                            e['first_name'], e['last_name']])
    payload = FileWrapper(file(path))
    expose_download(payload, expiry,
                    mimetype="application/octet-stream",
                    content_disposition='attachment; filename=export_webusage.csv',
                    download_id=download_id)    
