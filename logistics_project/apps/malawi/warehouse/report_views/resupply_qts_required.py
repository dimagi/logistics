
from logistics_project.apps.malawi.warehouse.report_views import warehouse

class View(warehouse.WarehouseView):

	def get_context(self, request):
	    ret_obj = {}

	    table = {
	        "title": "All Products (Aggregated Quantity required to ensure that HC can resupply",
	        "header": ["Facility Name", "%HSA with Stockout", "LA 1x6", "LA 2x6", "Zinc"],
	        "data": [['BULA', 32, 4123, 512, 3123], ['Chesamu', 22, 2123, 423, 123], ['Chikwina', 45, 4123, 423, 612]],
	        "cell_width": "135px",
	    }

	    ret_obj['table'] = table
	    return ret_obj
