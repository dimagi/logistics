from logistics_project.apps.malawi.warehouse.report_views import warehouse

class View(warehouse.WarehouseView):

	def get_context(self, request):
	    ret_obj = {}

	    table = {
	        "title": "Current Alert Summary",
	        "header": ["Facility", "# HSA", "%HSA stocked out", "%HSA with EO", "%HSA with no Products"],
	        "data": [['BULA', 332, 42, 53, 35], ['Chesamu', 232, 25, 41, 11], ['Chikwina', 443, 41, 41, 46]],
	        "cell_width": "135px",
	    }
	    
	    ret_obj['table'] = table
	    return ret_obj