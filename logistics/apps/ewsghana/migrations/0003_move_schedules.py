# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models
from rapidsms.contrib.scheduler.models import EventSchedule

class Migration(DataMigration):
    def forwards(self, orm):
        def _rename(schedule, new_schedule):
            try:
                es = EventSchedule.objects.get(callback=schedule)
            except EventSchedule.DoesNotExist:
                # must be malawi
                pass
            else:
                es.callback = new_schedule
                es.save()            
                
        _rename("logistics.apps.logistics.schedule.first_soh_reminder", 
                "logistics.apps.ewsghana.schedule.first_soh_reminder")
        _rename("logistics.apps.logistics.schedule.second_soh_reminder", 
                "logistics.apps.ewsghana.schedule.second_soh_reminder")
        _rename("logistics.apps.logistics.schedule.third_soh_to_super", 
                "logistics.apps.ewsghana.schedule.third_soh_to_super")
        _rename("logistics.apps.logistics.schedule.reminder_to_submit_RRIRV", 
                "logistics.apps.ewsghana.schedule.reminder_to_submit_RRIRV")

    def backwards(self, orm):
        pass
        #raise RuntimeError("Cannot reverse this migration.")

    models = {
        
    }

    complete_apps = ['ewsghana']
