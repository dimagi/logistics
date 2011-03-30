""" This is the glue that links views from logistics apps into email-able reports """

from logistics.apps.logistics.views import stockonhand_facility, district, reporting, aggregate
from logistics.apps.reports.schedule import ReportSchedule

STOCKONHAND_REPORT = ReportSchedule(stockonhand_facility,
                                     title="Facility Stock On Hand")
DISTRICT_REPORT = ReportSchedule(district,
                                  title="District Report")
REPORTING_REPORT = ReportSchedule(reporting,
                                   title="Reporting Rates")
AGGREGATE_REPORT = ReportSchedule(aggregate,
                                   title="Aggregate Stock Report")

SCHEDULABLE_REPORTS = {"stockonhand": STOCKONHAND_REPORT,
                       "district": DISTRICT_REPORT,
                       "reporting": REPORTING_REPORT,
                       "aggregate": AGGREGATE_REPORT,
                       }
