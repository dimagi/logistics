from builtins import str
from celery.schedules import crontab
from celery.decorators import periodic_task
from logistics_project.apps.malawi.nag import nag_hsas_em, nag_hsas_ept, nag_hsas_rec
from datetime import datetime
from django.conf import settings


@periodic_task(run_every=crontab(hour="*", minute="1", day_of_week="*"))
def nag_hsas():
    nag_hsas_ept()
    nag_hsas_em()
    nag_hsas_rec()

@periodic_task(run_every=crontab(hour="*", minute="*", day_of_week="*"))
def heartbeat():
    with open(settings.CELERY_HEARTBEAT_FILE, 'w') as f:
        f.write(str(datetime.now()))
    