from logistics_project.apps.malawi.warehouse import warehouse_view

class View(warehouse_view.MalawiWarehouseView):

	def get_context(self, request):
	    ret_obj = {}

	    table = {
	        "id": "current-alert-summary",
	        "is_datatable": False,
	        "header": ["Facility", "# HSA", "%HSA stocked out", "%HSA with EO", "%HSA with no Products"],
	        "data": [['BULA', 332, 42, 53, 35], ['Chesamu', 232, 25, 41, 11], ['Chikwina', 443, 41, 41, 46]],
	    }
	    
	    ret_obj['table'] = table
	    return ret_obj