from random import random

from logistics_project.apps.malawi.warehouse import warehouse_view

class View(warehouse_view.MalawiWarehouseView):

    def get_context(self, request):
        ret_obj = {}

        table1 = {
            "id": "district-consumption-profiles",
            "is_datatable": False,
            "header": ["Product", "Total Calc Cons", "Av Rep Rate", "AMC", "Total SOH"],
            "data": [['cc', 312, "47%", 5, 354], ['dt', 1322, "21%", 4, 121], ['sr', 4123, "14%", 4, 634]],
        }

        table2 = {
            "id": "facility-consumption-profiles",
            "is_datatable": False,
            "header": ["Product", "Total Calc Cons", "Av Rep Rate", "AMC", "Total SOH"],
            "data": [['cc', 3234, "40%", 5, 345], ['dt', 2123, "52%", 4, 111], ['sr', 4132, "43%", 4, 634]],
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

        ret_obj['table1'] = table1
        ret_obj['table2'] = table2
        ret_obj['line'] = line_chart
        return ret_obj