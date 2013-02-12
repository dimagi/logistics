import os
import tempfile
from celery.task import task
from django.core.servers.basehttp import FileWrapper
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
        f.write("%s\n" % ", ".join(["Date ", "User", "Access_Type",
                                         "Designation", "Organization", 
                                         "Facility", "Location", "First_Name", 
                                         "Last_Name"]))
        for e in detailedEvents:
            f.write("%s, " % e['date'])
            f.write("%s, " % e['user'])
            f.write("%s, " % e['class'])
            f.write("%s, " % e['designation'])
            f.write("%s, " % e['organization'])
            f.write("%s, " % e['facility'])
            f.write("%s, " % e['location'])
            f.write("%s, " % e['first_name'])
            f.write("%s\n" % e['last_name'])
    payload = FileWrapper(file(path))
    expose_download(payload, expiry,
                    mimetype="application/octet-stream",
                    content_disposition='attachment; filename=export.xls',
                    download_id=download_id)    
