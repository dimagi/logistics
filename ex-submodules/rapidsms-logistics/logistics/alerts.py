from __future__ import absolute_import
from datetime import datetime, timedelta
from alerts import Alert
from django.core.urlresolvers import reverse
from logistics.decorators import place_in_request, return_if_place_not_set
from logistics.reports import get_reporting_and_nonreporting_facilities

class NonReportingFacilityAlert(Alert):
    def __init__(self, facility):
        self._facility = facility
        super(NonReportingFacilityAlert, self).__init__(self._get_text(), 
                                                        reverse('reporting', 
                                                                args=(self._facility.location.code, )))

    def _get_text(self):
        return "%(facility)s has not reported in the last month." % \
               {'facility': self._facility.name}

@place_in_request()
def non_reporting_facilities(request):
    on_time, late = get_reporting_and_nonreporting_facilities(datetime.utcnow() - timedelta(days=32), 
                                                              location=request.location)
    if not late:
        return None
    return [NonReportingFacilityAlert(facility) for facility in late]

class FacilitiesWithoutRemindersAlert(Alert):
    def __init__(self, supply_point ):
        self._supply_point = supply_point
        super(FacilitiesWithoutRemindersAlert, self).__init__(self._get_text(), 
                                                              reverse("facility_detail", 
                                                                      args=(supply_point.code, )))

    def _get_text(self):
        return "%(place)s has no reminders configured." % \
                {"place": self._supply_point.name}

@place_in_request()
@return_if_place_not_set()
def facilities_without_reminders(request):
    facilities = request.location.all_child_facilities()
    if not facilities:
        return None
    return [FacilitiesWithoutRemindersAlert(facility) for facility in facilities \
            if facility.reporters().filter(needs_reminders=True).count() == 0]

class FacilitiesWithoutReportersAlert(Alert):
    def __init__(self, supply_point ):
        self._supply_point = supply_point
        super(FacilitiesWithoutReportersAlert, self).__init__(self._get_text(), 
                                                              reverse("facility_detail", 
                                                                      args=(self._supply_point.code, )))

    def _get_text(self):
        return "%(place)s has no reporters registered." % \
                {"place": self._supply_point.name}

@place_in_request()
@return_if_place_not_set()
def facilities_without_reporters(request):
    facilities = request.location.all_child_facilities()
    if not facilities:
        return None
    return [FacilitiesWithoutReportersAlert(facility) for facility in facilities \
            if (facility.reporters().count() == 0)]
