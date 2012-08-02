from random import random


def barseries(labels, num_points):
    return [{"label": l, "data": bardata(num_points)} for l in labels]
    
def bardata(num_points):
    return [[i + 1, random()] for i in range(num_points)]

#^^^^^junk

from logistics.models import Product

from logistics_project.apps.malawi.warehouse import warehouse_view

class View(warehouse_view.MalawiWarehouseView):

    def get_context(self, request):
        ret_obj = {}
        summary = {
            "number": 3,
            "xlabels": [],
            "legenddiv": "legend-div",
            "div": "chart-div",
            "max_value": 3,
            "width": "100%",
            "height": "200px",
            "data": [],
            "xaxistitle": "products",
            "yaxistitle": "amount"
        }
        
        product_codes = []

        count = 0
        for product in Product.objects.all().order_by('sms_code')[0:10]:
            count += 1
            product_codes.append([count, '<span>%s</span>' % (str(product.code.lower()))])
            
        summary['xlabels'] = product_codes
        
        summary['data'] = barseries(['Stocked Out','Under Stock','Adequate'], 10)

        table1 = {
            "title": "",
            "header": ["Product", "HSA Stocked Out", "HSA Under", "HSA Adequate", "Overstock"],
            "data": [['cc', 34, 45, 52, 31], ['dt', 21, 25, 44, 17], ['sr', 43, 44, 41, 67]],
            "cell_width": "135px",
        }

        table2 = {
            "title": "HSA Current Stock Status by District",
            "header": ["District", "HSA Stocked Out", "HSA Under", "HSA Adequate", "Overstock"],
            "data": [['cc', 33, 45, 52, 31], ['dt', 21, 29, 45, 13], ['sr', 43, 42, 42, 61]],
            "cell_width": "135px",
        }

        line_chart = {
            "height": "350px",
            "width": "100%", # "300px",
            "series": [],
        }
        for j in ['LA 1x6', 'LA 2x6']:
            temp = []
            for i in range(0,5):
                temp.append([random(),random()])
            line_chart["series"].append({"title": j, "data": sorted(temp)})

        ret_obj['summary'] = summary
        ret_obj['table1'] = table1
        ret_obj['table2'] = table2
        ret_obj['line'] = line_chart
        return ret_obj