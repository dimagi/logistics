from random import random
from datetime import datetime

from logistics_project.apps.malawi.warehouse import warehouse_view
from logistics_project.apps.malawi.warehouse.models import Consumption
from django.db.models import Sum
from dimagi.utils.dates import first_of_next_month, delta_secs, months_between,\
    secs_to_days
from logistics.models import SupplyPoint, Product
from logistics_project.apps.malawi.util import get_default_supply_point,\
    fmt_or_none, fmt_pct
from logistics.util import config

class View(warehouse_view.DistrictOnlyView):

    def custom_context(self, request):
        
        sp = SupplyPoint.objects.get(location=request.location) \
            if request.location else get_default_supply_point(request.user)
        
        table_headers = ["Product", "Total Actual Consumption for selected period",
                         "# stockout days for all HSAs", 
                         "Total consumption adjusted for stockouts", 
                         "Data Coverage", 
                         "Total Consumption (adjusted  for stockouts and data coverage)", 
                         "AMC  (for district for all HSAs)"]
        
        def _consumption_row(sp, p):
            
            relevant = Consumption.objects.filter(supply_point=sp, product=p,
                                                  date__gte=request.datespan.startdate,
                                                  date__lte=request.datespan.enddate)
            now = datetime.utcnow()
            end = first_of_next_month(request.datespan.enddate) \
                if request.datespan.enddate.year == now.year and \
                   request.datespan.enddate.month == now.month \
                else now
            vals = relevant.aggregate(Sum('calculated_consumption'), 
                                      Sum('time_stocked_out'),
                                      Sum('time_with_data'),
                                      Sum('time_needing_data'))
            tot_cons = vals['calculated_consumption__sum']
            tot_so_time = vals['time_stocked_out__sum']
            tot_time_with_data = vals['time_with_data__sum']
            tot_time_needing_data = vals['time_needing_data__sum']
            num_hsas = relevant[0].total
            avg_so_time = tot_so_time / num_hsas # NOTE: potential divide by 0
            period_secs = delta_secs(end - request.datespan.startdate)
            assert period_secs >= avg_so_time
            adjusted_secs = period_secs - avg_so_time
            so_adjusted_cons = tot_cons * (period_secs / adjusted_secs)
            
            scale_factor = float(tot_time_with_data) / float(tot_time_needing_data) \
                 if tot_time_needing_data != 0 else 0
            data_adjusted_cons = so_adjusted_cons / scale_factor \
                if scale_factor != 0 else so_adjusted_cons 
            amc = data_adjusted_cons / len(months_between(request.datespan.startdate,
                                                          request.datespan.enddate))
            _f = lambda x: fmt_or_none(x, percent=False)
            _f2 = lambda x: fmt_or_none(x * 100., percent=True)
            return [p.name, tot_cons, _f(secs_to_days(avg_so_time)), 
                    _f(so_adjusted_cons), _f2(scale_factor), 
                    _f(data_adjusted_cons), _f(amc)]
        
        d = f = d_table = f_table = None
        if sp.type.code == config.SupplyPointCodes.DISTRICT:
            d = sp
        elif sp.type.code == config.SupplyPointCodes.FACILITY:
            d = sp.supplied_by
            f = sp
        if d:
            d_table = {
                "id": "district-consumption-profiles",
                "is_datatable": False,
                "header": table_headers,
                "data": [_consumption_row(d, p) for p in Product.objects.all()]
            }
        if f:
            d_table = {
                "id": "facility-consumption-profiles",
                "is_datatable": False,
                "header": table_headers,
                "data": [_consumption_row(f, p) for p in Product.objects.all()]
            }
        
        line_chart = {
            "height": "350px",
            "width": "100%", # "300px",
            "series": [],
        }
        for j in ['Av Monthly Cons', 'Av Months of Stock']:
            temp = []
            for i in range(0,5):
                temp.append([random(),random()])
            line_chart["series"].append({"title": j, "data": sorted(temp)})

        return {
            "district_table": d_table,
            "facility_table": f_table,
            "line": line_chart
        }
