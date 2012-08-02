def timechart(labels):
    summary = {
        "number": 3,
        "xlabels": [],
        "legenddiv": "legend-div",
        "div": "chart-div",
        "max_value": 3,
        # "width": "730px",
        "width": "100%",
        "height": "200px",
        "data": [],
        "xaxistitle": "month",
        "yaxistitle": "rate"
    }
    count = 0
    summary['xlabels'] = month_labels(datetime.now() - timedelta(days=61), datetime.now())
    summary['data'] = barseries(labels, len(summary['xlabels']))
    return summary


def barseries(labels, num_points):
    return [{"label": l, "data": bardata(num_points)} for l in labels]
    
def bardata(num_points):
    return [[i + 1, random()] for i in range(num_points)]

from random import random

#^^^^^^^^^^^junk

from datetime import datetime, timedelta

from dimagi.utils.dates import months_between

from logistics_project.apps.malawi.warehouse.report_utils import month_labels
from logistics_project.apps.malawi.warehouse.report_views import warehouse

class View(warehouse.WarehouseView):

    def get_context(self, request):
        month_table = {
            "title": "",
            "header": ['Month', 'Ord-Ord Ready (days)', 'Ord-Ord Received(days)', 'Total Lead Time (days)'],
            "data": [['Jan', 3, 14, 7], ['Feb', 12, 7, 4], ['Mar', 14, 6, 4]],
        }

        lt_table = {
            "title": "Average Lead Times by Facility",
            "header": ['Facility', 'Period (# Months)', 'Ord-Ord Ready (days)', 'Ord-Ord Received(days)', 'Total Lead Time (days)'],
            "data": [['BULA', 6, 31, 42, 37], ['Chesamu', 6, 212, 27, 14], ['Chikwina', 6, 143, 61, 14]],
        }    
        return {"summary": timechart(['Ord-Ord Ready', 'Ord-Ord Received']),
                "month_table": month_table,
                "lt_table": lt_table}
