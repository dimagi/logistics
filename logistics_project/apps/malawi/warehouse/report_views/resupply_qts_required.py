
from logistics_project.apps.malawi.warehouse import warehouse_view

class View(warehouse_view.MalawiWarehouseView):

	def get_context(self, request):
	    ret_obj = {}

	    table = {
	        "id": "quantity-required-for-resupply",
	        "is_datatable" : False,
	        "header": ["Facility Name", "%HSA with Stockout", "LA 1x6", "LA 2x6", "Zinc"],
	        "data": [['BULA', 32, 4123, 512, 3123], ['Chesamu', 22, 2123, 423, 123], ['Chikwina', 45, 4123, 423, 612]],
	    }

	    ret_obj['table'] = table
	    return ret_obj
