from datetime import datetime

from django.db.models import Sum

from dimagi.utils.dates import first_of_next_month, delta_secs, months_between,\
    secs_to_days

from logistics.models import SupplyPoint, Product

from logistics_project.apps.malawi.warehouse import warehouse_view
from logistics_project.apps.malawi.warehouse.models import CalculatedConsumption
from logistics_project.apps.malawi.warehouse.report_utils import get_consumption_chart
from logistics_project.apps.malawi.util import get_default_supply_point,\
    fmt_or_none, hsa_supply_points_below, is_country, is_district,\
    is_facility

def consumption_row(sp, p, datespan):
            
    relevant = CalculatedConsumption.objects.filter(supply_point=sp, product=p,
                                                    date__gte=datespan.startdate,
                                                    date__lte=datespan.enddate)
    now = datetime.utcnow()
    end = now if datespan.enddate.year == now.year and \
                 datespan.enddate.month == now.month \
              else first_of_next_month(datespan.enddate)
    
    vals = relevant.aggregate(Sum('calculated_consumption'), 
                              Sum('time_stocked_out'),
                              Sum('time_with_data'),
                              Sum('time_needing_data'))
    tot_cons = vals['calculated_consumption__sum'] or 0
    tot_so_time = vals['time_stocked_out__sum'] or 0
    tot_time_with_data = vals['time_with_data__sum'] or 0
    tot_time_needing_data = vals['time_needing_data__sum'] or 0

    num_hsas = 0
    avg_so_time = 0
    if relevant.count() > 0:
        if relevant[0].total:
            num_hsas = relevant[0].total
            avg_so_time = tot_so_time / num_hsas

    period_secs = delta_secs(end - datespan.startdate)
    assert period_secs >= avg_so_time
    adjusted_secs = period_secs - avg_so_time
    so_adjusted_cons = (tot_cons * (period_secs / adjusted_secs)) if adjusted_secs else 0 
    
    scale_factor = float(tot_time_with_data) / float(tot_time_needing_data) \
         if tot_time_needing_data != 0 else 0
    data_adjusted_cons = so_adjusted_cons / scale_factor \
        if scale_factor != 0 else so_adjusted_cons 
    amc = data_adjusted_cons / len(months_between(datespan.startdate,
                                                  datespan.enddate))
    _f = lambda x: fmt_or_none(x, percent=False)
    _f2 = lambda x: fmt_or_none(x * 100., percent=True)
    return [p.name, tot_cons, _f(secs_to_days(avg_so_time)), 
            _f(so_adjusted_cons), _f2(scale_factor), 
            _f(data_adjusted_cons), _f(amc)]



class View(warehouse_view.DistrictOnlyView):

    def custom_context(self, request):
        
        sp = SupplyPoint.objects.get(location=request.location) \
            if request.location else get_default_supply_point(request.user)
        
        table_headers = ["Product", "Total Actual Consumption for selected period",
                         "# stockout days for all HSAs", 
                         "Total consumption adjusted for stockouts", 
                         "Data coverage (% of period)", 
                         "Total consumption (adjusted  for stockouts and data coverage)", 
                         "AMC for all HSAs"]
        
        hsa_list = selected_hsa = hsa_table = None
        
        if is_country(sp):
            type = "national"
        elif is_district(sp):
            type = "district"
        else:
            assert is_facility(sp)
            type = "facility"
            hsa_list = hsa_supply_points_below(sp.location)
            hsa_id = request.GET.get("hsa", "")
            if hsa_id:
                selected_hsa = SupplyPoint.objects.get(code=hsa_id) 
                hsa_table = {
                    "id": "hsa-consumption-profiles",
                    "is_datatable": False,
                    "is_downloadable": True,
                    "header": table_headers,
                    "data": [consumption_row(selected_hsa, p, request.datespan) for p in Product.objects.all()]
                }
            
        
        l_table = {
            "id": "location-consumption-profiles",
            "location_type": type,
            "is_datatable": False,
            "is_downloadable": True,
            "header": table_headers,
            "data": [consumption_row(sp, p, request.datespan) for p in Product.objects.all()]            
        }
            
        p_code = request.REQUEST.get("product", "")
        
        p = Product.objects.get(sms_code=p_code) if p_code else Product.objects.all()[0]
        line_chart = get_consumption_chart(sp, p, request.datespan.startdate, 
                                           request.datespan.enddate)
        return {
            "location_table": l_table,
            "hsa_table": hsa_table,
            "hsa_list": hsa_list,
            "selected_hsa": selected_hsa,
            "line_chart": line_chart,
            "selected_product": p
        }
