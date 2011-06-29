from celery.schedules import crontab
from celery.decorators import periodic_task
from logistics.apps.malawi.nag import nag_hsas_em, nag_hsas_ept
from datetime import datetime
import os
from django.conf import settings


@periodic_task(run_every=crontab(hour="*", minute="1", day_of_week="*"))
def nag_hsas():
    nag_hsas_ept()
    nag_hsas_em()

@periodic_task(run_every=crontab(hour="*", minute="*", day_of_week="*"))
def heartbeat():
    f = open(settings.CELERY_HEARTBEAT_FILE, 'w')
    f.write(str(datetime.now()))
    f.close()